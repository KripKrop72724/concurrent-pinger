import time


# Coroutine to ping a host and measure response time
async def ping_host(session, host):
    url = f'http://{host}'  # Construct the URL to ping
    start_time = time.time()  # Record the start time
    try:
        # Send an asynchronous GET request
        async with session.get(url) as response:
            # If the response status is 200 (OK)
            if response.status == 200:
                latency = time.time() - start_time  # Calculate the latency
                print(f'Ping to {host} successful: {latency:.4f} seconds')
            else:
                print(f'Ping to {host} failed with status code {response.status}')
    except Exception as e:
        print(f'Ping to {host} failed: {e}')
