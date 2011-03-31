# Copuright (c) 2011 Jyrki Pulliainen <jyrki@dywypi.org>
# Copyright (c) 2010 Inoi Oy
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
