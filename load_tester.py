import aiohttp
import asyncio
import time
import statistics
import random

URL_TO_TEST = ""
INITIAL_USERS = 10
MAX_USERS = 100000
ERROR_RATE_THRESHOLD = 0.10
RESPONSE_TIME_THRESHOLD = 10.0
TEST_DURATION = 10
THINK_TIME_MIN = 2.0
THINK_TIME_MAX = 10.0
MULTIPLIER = 2

# Global tracking
total_requests = 0
total_failures = 0

async def make_request(session):
    """Make a single HTTP request with realistic think time."""
    global total_requests, total_failures
    await asyncio.sleep(random.uniform(THINK_TIME_MIN, THINK_TIME_MAX))
    try:
        start_time = time.time()
        async with session.get(URL_TO_TEST) as response:
            total_requests += 1
            if response.status != 200:
                total_failures += 1
            return time.time() - start_time
    except Exception:
        total_failures += 1
        return float('inf')

async def simulate_user(session, duration):
    """Simulate a user making requests for a specified duration."""
    start_time = time.time()
    response_times = []
    while time.time() - start_time < duration:
        rt = await make_request(session)
        if rt != float('inf'):
            response_times.append(rt)
    return response_times

async def run_load_test(concurrent_users, test_duration):
    """Run a load test with specified concurrent users for a set duration."""
    global total_requests, total_failures
    before_requests = total_requests
    before_failures = total_failures
    async with aiohttp.ClientSession() as session:
        tasks = [simulate_user(session, test_duration) for _ in range(concurrent_users)]
        all_response_times = await asyncio.gather(*tasks)
    response_times = [rt for user_rts in all_response_times for rt in user_rts]
    valid_response_times = [rt for rt in response_times if rt != float('inf')]
    current_requests = total_requests - before_requests
    current_failures = total_failures - before_failures
    run_time = test_duration
    return {
        "response_times": valid_response_times,
        "requests": current_requests,
        "failures": current_failures,
        "run_time": run_time
    }

async def determine_load_capacity():
    """Determine the website's load capacity with dynamic ramp-up and fine-tuning."""
    current_users = INITIAL_USERS
    max_stable = 0
    print("Starting load capacity test...\n")
    while True:
        if current_users > MAX_USERS:
            break
        print(f"Testing {current_users} users for {TEST_DURATION} seconds...")
        result = await run_load_test(current_users, TEST_DURATION)
        # Calculate metrics
        response_times = result["response_times"]
        median_response_time = statistics.median(response_times) if response_times else float('inf')
        p95_response_time = statistics.quantiles(response_times, n=20)[-1] if response_times else float('inf')
        error_rate = result["failures"] / result["requests"] if result["requests"] > 0 else 0
        throughput = result["requests"] / result["run_time"] if result["run_time"] > 0 else 0
        # Report metrics
        print(f"  Median Response Time: {median_response_time * 1000:.2f} ms")
        print(f"  95th Percentile Response Time: {p95_response_time * 1000:.2f} ms")
        print(f"  Error Rate: {error_rate:.2%}")
        print(f"  Throughput: {throughput:.2f} req/s")
        # Check degradation
        degradation = (error_rate > ERROR_RATE_THRESHOLD or median_response_time > RESPONSE_TIME_THRESHOLD)
        if not degradation:
            max_stable = current_users
            next_users = current_users * MULTIPLIER
            if next_users > MAX_USERS:
                if current_users < MAX_USERS:
                    current_users = MAX_USERS
                else:
                    break
            else:
                current_users = next_users
        else:
            break
    # Fine-tuning phase
    if degradation and max_stable < current_users:
        low = max_stable
        high = current_users
        while low < high:
            mid = (low + high + 1) // 2
            print(f"Fine-tuning: Testing {mid} users for {TEST_DURATION} seconds...")
            result = await run_load_test(mid, TEST_DURATION)
            response_times = result["response_times"]
            median_response_time = statistics.median(response_times) if response_times else float('inf')
            error_rate = result["failures"] / result["requests"] if result["requests"] > 0 else 0
            degradation = (error_rate > ERROR_RATE_THRESHOLD or median_response_time > RESPONSE_TIME_THRESHOLD)
            if not degradation:
                low = mid
            else:
                high = mid - 1
        max_stable = low
    return max_stable

async def main():
    """Main function to run the load test."""
    max_stable_users = await determine_load_capacity()
    print(f"\nFinal maximum stable user count: {max_stable_users}")
    await asyncio.sleep(1.0)  # Allow transport cleanup

if __name__ == "__main__":
    asyncio.run(main())