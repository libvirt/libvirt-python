import asyncio
import libvirt
import libvirtaio
import sys
import unittest
from unittest import mock

import eventmock


class TestLibvirtAio(unittest.TestCase):
    async def _run(self, register):
        def lifecycleCallback(conn, dom, event, detail, domainChangedEvent):
            if (event == libvirt.VIR_DOMAIN_EVENT_STOPPED or
                    event == libvirt.VIR_DOMAIN_EVENT_STARTED):
                domainChangedEvent.set()

        if register:
            libvirtEvents = libvirtaio.virEventRegisterAsyncIOImpl()
        else:
            libvirtEvents = libvirtaio.getCurrentImpl()

        conn = libvirt.open("test:///default")
        dom = conn.lookupByName("test")

        eventRegistered = False
        domainStopped = False
        try:
            # Ensure the VM is running.
            self.assertEqual([libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_RUNNING_UNKNOWN], dom.state())
            self.assertTrue(libvirtEvents.is_idle())

            # Register VM start/stopped event handler.
            domainChangedEvent = asyncio.Event()
            conn.domainEventRegisterAny(dom, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, lifecycleCallback, domainChangedEvent)
            eventRegistered = True

            self.assertFalse(libvirtEvents.is_idle())

            # Stop the VM.
            dom.destroy()
            domainStopped = True

            # Ensure domain stopped event is received.
            await asyncio.wait_for(domainChangedEvent.wait(), 2)
            self.assertEqual([libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_SHUTOFF_DESTROYED], dom.state())

            # Start the VM.
            domainChangedEvent.clear()
            domainStopped = False
            dom.create()

            # Ensure domain started event is received.
            await asyncio.wait_for(domainChangedEvent.wait(), 2)
            self.assertEqual([libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_RUNNING_BOOTED], dom.state())
            self.assertFalse(libvirtEvents.is_idle())

            # Deregister the VM start/stopped event handler.
            eventRegistered = False
            conn.domainEventDeregisterAny(libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE)

            # Wait for event queue to clear.
            await libvirtEvents.drain()

            # Make sure event queue is cleared.
            self.assertTrue(libvirtEvents.is_idle())

        finally:
            if eventRegistered:
                conn.domainEventDeregisterAny(libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE)

            if domainStopped:
                dom.create()

    @mock.patch('libvirt.virEventRegisterImpl',
                side_effect=eventmock.virEventRegisterImplMock)
    def testEventsWithManualLoopSetup(self, mock_event_register):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._run(register=True))

        loop.close()
        asyncio.set_event_loop(None)
        mock_event_register.assert_called_once()

    @mock.patch('libvirt.virEventRegisterImpl',
                side_effect=eventmock.virEventRegisterImplMock)
    @unittest.skipIf(sys.version_info < (3,7), "test requires Python 3.7+")
    def testEventsWithAsyncioRun(self, mock_event_register):
        asyncio.run(self._run(register=True))
        mock_event_register.assert_called_once()

    @mock.patch('libvirt.virEventRegisterImpl',
                side_effect=eventmock.virEventRegisterImplMock)
    @unittest.skipIf(sys.version_info >= (3,10), "test not compatible with Python 3.10+")
    def testEventsPreInit(self, mock_event_register):
        # Initialize libvirt events before setting the event loop. This is not recommended.
        # But is supported in older version of Python for the sake of back-compat.
        loop = asyncio.new_event_loop()
        libvirtaio.virEventRegisterAsyncIOImpl(loop)
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._run(register=False))

        loop.close()
        asyncio.set_event_loop(None)
        mock_event_register.assert_called_once()

    @mock.patch('libvirt.virEventRegisterImpl',
                side_effect=eventmock.virEventRegisterImplMock)
    def testEventsImplicitLoopInit(self, mock_event_register):
        # Allow virEventRegisterAsyncIOImpl() to init the event loop by calling
        # asyncio.get_event_loop(). This is not recommended and probably only works by
        # accident. But is supported for now for the sake of back-compat. For Python
        # 3.10+, asyncio will report deprecation warnings.
        libvirtaio.virEventRegisterAsyncIOImpl()
        loop = asyncio.get_event_loop()

        loop.run_until_complete(self._run(register=False))

        loop.close()
        asyncio.set_event_loop(None)
        mock_event_register.assert_called_once()
