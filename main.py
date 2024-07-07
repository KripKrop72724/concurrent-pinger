import asyncio
import os
import aiohttp
import sys
from reader import read_hosts
from pinger import ping_host


# Main coroutine to orchestrate the ping tasks
async def main():
    try:
        hosts = read_hosts('hosts.txt')  # Read hosts from file
        async with aiohttp.ClientSession() as session:  # Manage the HTTP session
            tasks = [ping_host(session, host) for host in hosts]  # Create a list of tasks
            await asyncio.gather(*tasks)  # Run all tasks concurrently
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        sys.exit(1)  # Exit the program with an error code


# Entry point of the script
if __name__ == '__main__':
    if os.name == 'nt':  # Check if the OS is Windows
        # checking ig the os is windows and making sure that the ProactorEventLoop is not being used by default
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())  # Run the main coroutine
