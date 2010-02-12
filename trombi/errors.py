# Collection of possible couchdb errors
CONFLICT = 409
PRECONDITION_FAILED = 412
NOT_FOUND = 404
SERVER_ERROR = 500

# Non-http errors (or overloaded http 500 errors)
INVALID_DATABASE_NAME = 51

errormap = {
    409: CONFLICT,
    412: PRECONDITION_FAILED,
    404: NOT_FOUND,
    500: SERVER_ERROR
    }
