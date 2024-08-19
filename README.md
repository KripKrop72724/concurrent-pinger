# Async Ping Utility

This project is an asynchronous ping utility written in Python. It utilizes the `asyncio` and `aiohttp` libraries to perform concurrent HTTP GET requests to a list of hosts, measuring and reporting the response times. The script reads hosts from a file (`hosts.txt`), pings each host asynchronously, and prints the latency for each successful ping. Exception handling ensures robustness, and the event loop policy is set to handle resource cleanup effectively on Windows.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Files](#files)
- [Event Loop Policy on Windows](#event-loop-policy-on-windows)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/async-ping-utility.git
    cd async-ping-utility
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**

    ```bash
    pip install aiohttp
    ```

## Usage

1. **Prepare the hosts file:**

    Create a file named `hosts.txt` in the project directory with the list of hosts that you want to ping. For example:

    ```
    google.com
    github.com
    stackoverflow.com
    python.org
    facebook.com
    ```

2. **Run the script:**

    ```bash
    python main.py
    ```

## Files

- **pinger.py:** Contains the function to ping a host and measure response time.
- **reader.py:** Contains the function to read hosts from a file.
- **main.py:** Contains the main function to orchestrate the ping tasks.

## pinger.py

```python
import asyncio
import aiohttp
import time

async def ping_host(session, host):
    url = f'http://{host}'
    start_time = time.time()
    try:
        async with session.get(url) as response:
            if response.status == 200:
                latency = time.time() - start_time
                print(f'Ping to {host} successful: {latency:.4f} seconds')
            else:
                print(f'Ping to {host} failed with status code {response.status}')
    except Exception as e:
        print(f'Ping to {host} failed: {e}')
```

## reader.py

```python
import os
import sys

def read_hosts(file_path):
    if not os.path.exists(file_path):
        print(f'Error: The file {file_path} does not exist.')
        sys.exit(1)
    try:
        with open(file_path, 'r') as file:
            hosts = file.read().splitlines()
        if not hosts:
            print(f'Error: The file {file_path} is empty.')
            sys.exit(1)
        return hosts
    except Exception as e:
        print(f'Error reading file {file_path}: {e}')
        sys.exit(1)
```

### main.py

```python
import asyncio
import aiohttp
import sys
from pinger import ping_host
from reader import read_hosts

async def main():
    try:
        hosts = read_hosts('hosts.txt')
        async with aiohttp.ClientSession() as session:
            tasks = [ping_host(session, host) for host in hosts]
            await asyncio.gather(*tasks)
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        sys.exit(1)

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

```
### Event Loop Policy on Windows

When running this script on Windows, you may encounter the following error:

Exception ignored in: <function _ProactorBasePipeTransport.del at 0x000002059A408550>
RuntimeError: Event loop is closed


This error is due to the default `ProactorEventLoop` on Windows, which can sometimes leave resources uncleaned when the event loop is closed quickly. To handle this issue, we set the event loop policy to `WindowsSelectorEventLoopPolicy`, which manages resource cleanup more effectively.

In `main.py`, we include the following code to set the event loop policy on Windows:

```python
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

```
