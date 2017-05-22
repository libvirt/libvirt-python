    def __del__(self):
        try:
            if self.cb:
                libvirtmod.virStreamEventRemoveCallback(self._o)
        except AttributeError:
           pass

        if self._o is not None:
            libvirtmod.virStreamFree(self._o)
        self._o = None

    def _dispatchStreamEventCallback(self, events, cbData):
        """
        Dispatches events to python user's stream event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, events, opaque)
        return 0

    def eventAddCallback(self, events, cb, opaque):
        self.cb = cb
        cbData = {"stream": self, "cb" : cb, "opaque" : opaque}
        ret = libvirtmod.virStreamEventAddCallback(self._o, events, cbData)
        if ret == -1: raise libvirtError ('virStreamEventAddCallback() failed')

    def recvAll(self, handler, opaque):
        """Receive the entire data stream, sending the data to the
        requested data sink. This is simply a convenient alternative
        to virStreamRecv, for apps that do blocking-I/O.

        A hypothetical handler function looks like:

            def handler(stream, # virStream instance
                        buf,    # string containing received data
                        opaque): # extra data passed to recvAll as opaque
                fd = opaque
                return os.write(fd, buf)
        """
        while True:
            got = self.recv(1024*64)
            if got == -2:
                raise libvirtError("cannot use recvAll with "
                                   "nonblocking stream")
            if len(got) == 0:
                break

            try:
                ret = handler(self, got, opaque)
                if type(ret) is int and ret < 0:
                    raise RuntimeError("recvAll handler returned %d" % ret)
            except Exception:
                e = sys.exc_info()[1]
                try:
                    self.abort()
                except:
                    pass
                raise e

    def sendAll(self, handler, opaque):
        """
        Send the entire data stream, reading the data from the
        requested data source. This is simply a convenient alternative
        to virStreamSend, for apps that do blocking-I/O.

        A hypothetical handler function looks like:

            def handler(stream, # virStream instance
                        nbytes, # int amt of data to read
                        opaque): # extra data passed to recvAll as opaque
                fd = opaque
                return os.read(fd, nbytes)
        """
        while True:
            try:
                got = handler(self, 1024*64, opaque)
            except:
                e = sys.exc_info()[1]
                try:
                    self.abort()
                except:
                    pass
                raise e

            if not got:
                break

            ret = self.send(got)
            if ret == -2:
                raise libvirtError("cannot use sendAll with "
                                   "nonblocking stream")

    def recv(self, nbytes):
        """Reads a series of bytes from the stream. This method may
        block the calling application for an arbitrary amount
        of time.

        Errors are not guaranteed to be reported synchronously
        with the call, but may instead be delayed until a
        subsequent call.

        On success, the received data is returned. On failure, an
        exception is raised. If the stream is a NONBLOCK stream and
        the request would block, integer -2 is returned.
        """
        ret = libvirtmod.virStreamRecv(self._o, nbytes)
        if ret is None: raise libvirtError ('virStreamRecv() failed')
        return ret

    def send(self, data):
        """Write a series of bytes to the stream. This method may
        block the calling application for an arbitrary amount
        of time. Once an application has finished sending data
        it should call virStreamFinish to wait for successful
        confirmation from the driver, or detect any error

        This method may not be used if a stream source has been
        registered

        Errors are not guaranteed to be reported synchronously
        with the call, but may instead be delayed until a
        subsequent call.
        """
        ret = libvirtmod.virStreamSend(self._o, data)
        if ret == -1: raise libvirtError ('virStreamSend() failed')
        return ret

    def recvHole(self, flags = 0):
        """This method is used to determine the length in bytes
        of the empty space to be created in a stream's target
        file when uploading or downloading sparsely populated
        files. This is the counterpart to sendHole.
        """
        ret = libvirtmod.virStreamRecvHole(self._o, flags)
        if ret is None: raise libvirtError ('virStreamRecvHole() failed')
        return ret

    def sendHole(self, length, flags = 0):
        """Rather than transmitting empty file space, this method
        directs the stream target to create length bytes of empty
        space.  This method would be used when uploading or
        downloading sparsely populated files to avoid the
        needless copy of empty file space.
        """
        ret = libvirtmod.virStreamSendHole(self._o, length, flags)
        if ret == -1: raise libvirtError('virStreamSendHole() failed')
        return ret

    def recvFlags(self, nbytes, flags = 0):
        """Reads a series of bytes from the stream. This method may
        block the calling application for an arbitrary amount
        of time. This is just like recv except it has flags
        argument.

        Errors are not guaranteed to be reported synchronously
        with the call, but may instead be delayed until a
        subsequent call.

        On success, the received data is returned. On failure, an
        exception is raised. If the stream is a NONBLOCK stream and
        the request would block, integer -2 is returned.
        """
        ret = libvirtmod.virStreamRecvFlags(self._o, nbytes, flags)
        if ret is None: raise libvirtError ('virStreamRecvFlags() failed')
        return ret

    def sparseRecvAll(self, handler, holeHandler, opaque):
        """Receive the entire data stream, sending the data to
        the requested data sink handler and calling the skip
        holeHandler to generate holes for sparse stream targets.
        This is simply a convenient alternative to recvFlags, for
        apps that do blocking-I/O and want to preserve sparseness.

        Hypothetical callbacks can look like this:

            def handler(stream, # virStream instance
                        buf,    # string containing received data
                        opaque): # extra data passed to sparseRecvAll as opaque
                fd = opaque
                return os.write(fd, buf)

            def holeHandler(stream, # virStream instance
                            length, # number of bytes to skip
                            opaque): # extra data passed to sparseRecvAll as opaque
                fd = opaque
                cur = os.lseek(fd, length, os.SEEK_CUR)
                return os.ftruncate(fd, cur) # take this extra step to
                                             # actually allocate the hole
        """
        while True:
            want = 64 * 1024
            got = self.recvFlags(want, VIR_STREAM_RECV_STOP_AT_HOLE)
            if got == -2:
                raise libvirtError("cannot use sparseRecvAll with "
                                   "nonblocking stream")
            if got == -3:
                length = self.recvHole()
                if length is None:
                    self.abort()
                    raise RuntimeError("recvHole handler failed")
                ret = holeHandler(self, length, opaque)
                if type(ret) is int and ret < 0:
                    self.abort()
                    raise RuntimeError("holeHandler handler returned %d" % ret)
                continue

            if len(got) == 0:
                break

            ret = handler(self, got, opaque)
            if type(ret) is int and ret < 0:
                self.abort()
                raise RuntimeError("sparseRecvAll handler returned %d" % ret)

    def sparseSendAll(self, handler, holeHandler, skipHandler, opaque):
        """Send the entire data stream, reading the data from the
        requested data source. This is simply a convenient
        alternative to virStreamSend, for apps that do
        blocking-I/O and want to preserve sparseness.

        Hypothetical callbacks can look like this:

            def handler(stream, # virStream instance
                        nbytes, # int amt of data to read
                        opaque): # extra data passed to sparseSendAll as opaque
                fd = opaque
                return os.read(fd, nbytes)

            def holeHandler(stream, # virStream instance
                            opaque): # extra data passed to sparseSendAll as opaque
                fd = opaque
                cur = os.lseek(fd, 0, os.SEEK_CUR)
                # ... find out current section and its boundaries
                # and set inData = True/False and sectionLen correspondingly
                os.lseek(fd, cur, os.SEEK_SET)
                return [inData, sectionLen]

            def skipHandler(stream, # virStream instance
                            length, # number of bytes to skip
                            opaque): # extra data passed to sparseSendAll as opaque
                fd = opaque
                return os.lseek(fd, length, os.SEEK_CUR)

        """
        while True:
            [inData, sectionLen] = holeHandler(self, opaque)
            if (inData == False and sectionLen > 0):
                if (self.sendHole(sectionLen) < 0 or
                        skipHandler(self, sectionLen, opaque) < 0):
                    self.abort()
                continue

            want = 64 * 1024
            if (want > sectionLen):
                want = sectionLen

            got = handler(self, want, opaque)
            if type(got) is int and got < 0:
                self.abort()
                raise RuntimeError("sparseSendAll handler returned %d" % ret)

            if not got:
                break

            ret = self.send(got)
            if ret == -2:
                raise libvirtError("cannot use sparseSendAll with "
                                   "nonblocking stream")
