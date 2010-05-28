# Copyright (c) Inoi Oy 2010. All rights reserved.
#
# This material constitutes a trade secret of Inoi Oy.
#
# The software, manuals, and technical literature of
# Inoi Oy products may not be reproduced in any form or
# by any means except by permission in writing from
# Inoi Oy.

# Collection of possible couchdb errors
BAD_REQUEST = 400
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
