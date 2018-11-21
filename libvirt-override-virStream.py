    def __del__(self) -> None:
        try:
            if self.cb:
                libvirtmod.virStreamEventRemoveCallback(self._o)
        except AttributeError:
            pass

        if self._o is not None:
            libvirtmod.virStreamFree(self._o)
        self._o = None

    def _dispatchStreamEventCallback(self, events: int, cbData: Dict[str, Any]) -> int:
        """
        Dispatches events to python user's stream event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, events, opaque)
        return 0

    def eventAddCallback(self, events: int, cb: Callable[['virStream', int, _T], None], opaque: _T) -> None:
        self.cb = cb
        cbData = {"stream": self, "cb": cb, "opaque": opaque}
        ret = libvirtmod.virStreamEventAddCallback(self._o, events, cbData)
        if ret == -1:
            raise libvirtError('virStreamEventAddCallback() failed')

    def recvAll(self, handler: Callable[['virStream', bytes, _T], int], opaque: _T) -> None:
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
            got = self.recv(virStorageVol.streamBufSize)
            if got == -2:
                raise libvirtError("cannot use recvAll with "
                                   "nonblocking stream")
            if len(got) == 0:
                break

            try:
                ret = handler(self, got, opaque)
                if isinstance(ret, int) and ret < 0:
                    raise RuntimeError("recvAll handler returned %d" % ret)
            except BaseException:
                try:
                    self.abort()
                except Exception:
                    pass
                raise

    def sendAll(self, handler: Callable[['virStream', int, _T], bytes], opaque: _T) -> None:
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
                got = handler(self, virStorageVol.streamBufSize, opaque)
            except BaseException:
                try:
                    self.abort()
                except Exception:
                    pass
                raise

            if not got:
                break

            ret = self.send(got)
            if ret == -2:
                raise libvirtError("cannot use sendAll with "
                                   "nonblocking stream")

    def recv(self, nbytes: int) -> bytes:
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
        if ret is None:
            raise libvirtError('virStreamRecv() failed')
        return ret

    def send(self, data: bytes) -> int:
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
        if ret == -1:
            raise libvirtError('virStreamSend() failed')
        return ret

    def recvHole(self, flags: int = 0) -> int:
        """This method is used to determine the length in bytes
        of the empty space to be created in a stream's target
        file when uploading or downloading sparsely populated
        files. This is the counterpart to sendHole.
        """
        ret = libvirtmod.virStreamRecvHole(self._o, flags)
        if ret is None:
            raise libvirtError('virStreamRecvHole() failed')
        return ret

    def sendHole(self, length: int, flags: int = 0) -> int:
        """Rather than transmitting empty file space, this method
        directs the stream target to create length bytes of empty
        space.  This method would be used when uploading or
        downloading sparsely populated files to avoid the
        needless copy of empty file space.
        """
        ret = libvirtmod.virStreamSendHole(self._o, length, flags)
        if ret == -1:
            raise libvirtError('virStreamSendHole() failed')
        return ret

    def recvFlags(self, nbytes: int, flags: int = 0) -> Union[bytes, int]:
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
        if ret is None:
            raise libvirtError('virStreamRecvFlags() failed')
        return ret

    def sparseRecvAll(self, handler: Callable[['virStream', bytes, _T], Union[bytes, int]], holeHandler: Callable[['virStream', int, _T], Optional[int]], opaque: _T) -> None:
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
            want = virStorageVol.streamBufSize
            got = self.recvFlags(want, VIR_STREAM_RECV_STOP_AT_HOLE)
            if got == -2:
                raise libvirtError("cannot use sparseRecvAll with "
                                   "nonblocking stream")
            elif got == -3:
                length = self.recvHole()
                if length is None:
                    self.abort()
                    raise RuntimeError("recvHole handler failed")
                ret_hole = holeHandler(self, length, opaque)
                if isinstance(ret_hole, int) and ret_hole < 0:
                    self.abort()
                    raise RuntimeError("holeHandler handler returned %d" % ret_hole)
                continue
            elif isinstance(got, int):
                raise ValueError(got)
            elif not isinstance(got, bytes):
                raise TypeError(type(got))

            if len(got) == 0:
                break

            ret_data = handler(self, got, opaque)
            if isinstance(ret_data, int) and ret_data < 0:
                self.abort()
                raise RuntimeError("sparseRecvAll handler returned %d" % ret_data)

    def sparseSendAll(self, handler: Callable[['virStream', int, _T], Union[bytes, int]], holeHandler: Callable[['virStream', _T], Tuple[bool, int]], skipHandler: Callable[['virStream', int, _T], int], opaque: _T) -> None:
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
            if not inData and sectionLen > 0:
                if (self.sendHole(sectionLen) < 0 or
                        skipHandler(self, sectionLen, opaque) < 0):
                    self.abort()
                continue

            want = virStorageVol.streamBufSize
            if (want > sectionLen):
                want = sectionLen

            got = handler(self, want, opaque)
            if isinstance(got, int) and got < 0:
                self.abort()
                raise RuntimeError("sparseSendAll handler returned %d" % got)

            if not got:
                break

            assert isinstance(got, bytes)
            ret = self.send(got)
            if ret == -2:
                raise libvirtError("cannot use sparseSendAll with "
                                   "nonblocking stream")
