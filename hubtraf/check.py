import asyncio
import structlog
import argparse
import random
import time
import socket
from hubtraf.user import User
from hubtraf.auth.dummy import login_dummy
from functools import partial
from collections import Counter
import secrets


async def no_auth(*args, **kwargs):
    return True

async def check_user(hub_url, username):
    async with User(username, hub_url, no_auth) as u:
        try:
            if not await u.ensure_server_api():
                return 'start-server'
            if not await u.start_kernel():
                return 'start-kernel'
            nonce = secrets.token_hex(64)
            if not await u.assert_code_output(f"!echo -n {nonce} > nonce \n!cat nonce", nonce, 2):
                return 'run-code'
        finally:
            if u.state == User.States.KERNEL_STARTED:
                if not await u.stop_kernel():
                    return 'stop-kernel'
            if u.state == User.States.SERVER_STARTED:
                if not await u.stop_server():
                    return 'stop-kernel'
            return 'completed'


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'hub_url',
        help='Hub URL to send traffic to (without a trailing /)'
    )
    argparser.add_argument(
        'username',
        help='Name of user to check'
    )
    args = argparser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_user(args.hub_url, args.username))


if __name__ == '__main__':
    main()