#!/usr/bin/python
import string
import random


""" This Library just retruns a usnique Session Id..
    # 0851742253
    # <mholbrook@eircom.ie>
    13/1/2017 :- Initial Draft.
"""


def id_generator(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


if __name__ == '__main__':
    main()
