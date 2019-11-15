import pytest

from insanic.conf import settings

from interstellar import config as common_config
from interstellar.server import InterstellarServer, config as server_config
# from interstellar.server.log import interstellar_server_error_log
# from interstellar.server.server import interstellar_request_handler
from interstellar.server.server.handlers import RequestHandler

from grpclib.encoding.proto import ProtoCodec


@pytest.fixture()
def mock_h2_stream():
    class MockStream:
        closable = False
        id = 4

        async def send_headers(self, headers, end_stream):
            pass

    return MockStream()


@pytest.fixture(autouse=True)
def load_settings():
    InterstellarServer.load_config(settings, common_config)
    InterstellarServer.load_config(settings, server_config)


class TestRequestHandlerErrors:

    async def test_method_error(self, mock_h2_stream, monkeypatch):
        headers = [(":method", "GET")]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" not in dict_headers
            assert "grpc-message" not in dict_headers

            assert dict_headers[':status'] == "405"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, None, None, object)

        result = await handler.handle()
        assert result is None
        assert len(send_header_called) > 0

    async def test_no_method_headers_error(self, mock_h2_stream, monkeypatch):
        headers = []

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" not in dict_headers
            assert "grpc-message" not in dict_headers

            assert dict_headers[':status'] == "405"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, None, None, object)
        result = await handler.handle()
        assert result is None
        # assert len(send_header_called) > 0

    async def test_content_type_missing_error(self, mock_h2_stream, monkeypatch):
        headers = [(":method", "POST")]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" in dict_headers
            assert "grpc-message" in dict_headers

            assert dict_headers[':status'] == "415"
            assert dict_headers['grpc-status'] == "2"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, None, None, object)
        result = await handler.handle()
        assert result is None
        assert len(send_header_called) > 0

    @pytest.mark.parametrize(
        "content_type",
        ("application/json",
         "application/grpc",
         "application/grpc+",
         "application/grpc+ape")
    )
    async def test_content_type_invalid_error(self, mock_h2_stream, monkeypatch, content_type):
        class MockCodec:
            __content_subtype__ = "asd"

        headers = [(":method", "POST"), ("content-type", content_type)]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" in dict_headers
            assert "grpc-message" in dict_headers

            assert dict_headers[':status'] == "415"
            assert dict_headers['grpc-status'] == "2"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, MockCodec(), None, object)
        result = await handler.handle()
        assert result is None
        assert len(send_header_called) > 0

    async def test_te_missing_error(self, mock_h2_stream, monkeypatch):
        headers = [(":method", "POST"), ("content-type", 'application/grpc+proto')]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" in dict_headers
            assert "grpc-message" in dict_headers

            assert dict_headers[':status'] == "400"
            assert dict_headers['grpc-status'] == "2"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, ProtoCodec(), None, object)
        result = await handler.handle()
        assert result is None
        assert len(send_header_called) > 0

    async def test_te_invalid_error(self, mock_h2_stream, monkeypatch):
        headers = [(":method", "POST"), ("content-type", 'application/grpc+proto'), ('te', "asda")]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" in dict_headers
            assert "grpc-message" in dict_headers

            assert dict_headers[':status'] == "400"
            assert dict_headers['grpc-status'] == "2"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, ProtoCodec(), None, object)
        result = await handler.handle()
        assert result is None
        assert len(send_header_called) > 0

    async def test_path_missing_error(self, mock_h2_stream, monkeypatch):
        headers = [(":method", "POST"), ("content-type", 'application/grpc+proto'),
                   ('te', "trailers")]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" in dict_headers
            assert "grpc-message" in dict_headers

            assert dict_headers[':status'] == "200"
            assert dict_headers['grpc-status'] == "12"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, ProtoCodec(), None, object)
        result = await handler.handle()
        assert result is None
        # assert len(send_header_called) > 0

    async def test_path_invalid_error(self, mock_h2_stream, monkeypatch):
        headers = [(":method", "POST"), ("content-type", 'application/grpc+proto'),
                   ('te', "trailers"), (':path', "asdad")]

        send_header_called = []

        async def mock_send_header(headers, end_stream):
            dict_headers = dict(headers)

            assert ":status" in dict_headers
            assert "grpc-status" in dict_headers
            assert "grpc-message" in dict_headers

            assert dict_headers[':status'] == "200"
            assert dict_headers['grpc-status'] == "12"

            send_header_called.append(True)

        monkeypatch.setattr(mock_h2_stream, 'send_headers', mock_send_header)

        handler = RequestHandler({}, mock_h2_stream, headers, ProtoCodec(), None, object)
        result = await handler.handle()
        assert result is None
        assert len(send_header_called) > 0
