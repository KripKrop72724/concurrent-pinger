import aiohttp
import asyncio
import time

# Global tracking variables
total_requests = 0
total_failures = 0
start_time = time.time()

# Intelligent dynamic adjustment variables
max_ramp_up_rate = 100  # Max number of users to add at a time
min_ramp_up_rate = 5  # Start ramp-up at a higher rate
adjustment_factor = 1.5  # More aggressive factor to scale ramp-up based on performance
ramp_up_rate = min_ramp_up_rate  # Initial rate of ramping up
error_rate_threshold = None  # Error rate threshold will be set dynamically
response_time_threshold = None  # Response time threshold will be set dynamically

# Fine-tuning variables
fine_tuning = False
last_good_user_count = 0
fine_tuning_attempts = 3  # Fine-tuning verification attempts
final_user_limit = 0

# URL to test
url_to_test = "https://example.com/"


# Function to simulate concurrent requests using aiohttp
async def make_request(session):
    global total_requests, total_failures
    try:
        start_request_time = time.time()
        async with session.get(url_to_test) as response:
            total_requests += 1
            if response.status != 200:
                total_failures += 1
                return time.time() - start_request_time
            return time.time() - start_request_time
    except Exception as e:
        total_failures += 1
        return float('inf')  # Return a high response time for failed requests


# Function to run the test
async def run_load_test(concurrent_users):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(concurrent_users):
            tasks.append(make_request(session))
        response_times = await asyncio.gather(*tasks)
    return response_times


# Function to monitor and adjust the load dynamically, with fine-tuning
async def intelligent_adjustment():
    global ramp_up_rate, total_requests, total_failures, start_time
    global error_rate_threshold, response_time_threshold, fine_tuning, last_good_user_count
    global final_user_limit, fine_tuning_attempts

    current_users = 28  # Start with 28 users to speed up initial testing
    last_good_user_count = current_users

    while True:
        # Simulate concurrent requests for current_users
        print(f"Testing with {current_users} users...")
        response_times = await run_load_test(current_users)

        # Calculate statistics
        elapsed_time = time.time() - start_time
        avg_response_time = sum(response_times) / len(response_times) if response_times else 1
        error_rate = total_failures / total_requests if total_requests > 0 else 0
        requests_per_second = total_requests / elapsed_time

        # Dynamically set error rate and response time thresholds
        if error_rate_threshold is None:
            error_rate_threshold = 0.05  # Set to 5% initially
        if response_time_threshold is None:
            response_time_threshold = avg_response_time * 1.5  # Set to 1.5x initial response time

        # Print current stats
        print(f"Users: {current_users}, Avg Response Time: {avg_response_time:.2f} ms, "
              f"Error Rate: {error_rate:.2%}, Requests/sec: {requests_per_second:.2f}")

        # Check if the server is breaking under load
        if avg_response_time > response_time_threshold or error_rate > error_rate_threshold:
            print(f"Performance degradation detected at {current_users} users.")

            if not fine_tuning:
                # Enter fine-tuning mode
                fine_tuning = True
                # Set the last successful user count and decrease user load for fine-tuning
                current_users = (last_good_user_count + current_users) // 2
                continue
            else:
                # If already fine-tuning and another failure occurs, finalize the user count
                print(f"Fine-tuning complete. Maximum stable user count is {last_good_user_count} users.")
                final_user_limit = last_good_user_count
                break  # Break out of the main loop for further verification attempts

        else:
            # If performance is good, store the last good user count
            last_good_user_count = current_users

        # Adjust ramp-up rate dynamically
        if avg_response_time < response_time_threshold * 0.7 and error_rate < error_rate_threshold * 0.5:
            # Server is performing well, ramp up aggressively
            ramp_up_rate = min(int(ramp_up_rate * (1 + adjustment_factor)), max_ramp_up_rate)
        else:
            # Server is struggling, slow down ramp-up
            ramp_up_rate = max(int(ramp_up_rate * (1 - adjustment_factor)), min_ramp_up_rate)

        # Ensure ramp-up rate does not get stuck too low
        ramp_up_rate = max(ramp_up_rate, min_ramp_up_rate)

        # Increase concurrent users based on ramp-up rate
        current_users += ramp_up_rate

        # Ensure we do not exceed too high a number of concurrent users
        if current_users > 1000:  # You can change this limit based on your use case
            print(f"Max users reached without failure. Test completed at {current_users} users.")
            break

        # Sleep for a shorter period before next batch to make the ramp-up faster
        await asyncio.sleep(2)


# Function to verify the fine-tuned value
async def verify_max_users():
    global final_user_limit, fine_tuning_attempts

    for attempt in range(fine_tuning_attempts):
        print(f"\nVerification Attempt {attempt + 1}: Testing with {final_user_limit} users...")
        response_times = await run_load_test(final_user_limit)

        # Calculate statistics
        elapsed_time = time.time() - start_time
        avg_response_time = sum(response_times) / len(response_times) if response_times else 1
        error_rate = total_failures / total_requests if total_requests > 0 else 0

        print(f"Users: {final_user_limit}, Avg Response Time: {avg_response_time:.2f} ms, "
              f"Error Rate: {error_rate:.2%}")

        if avg_response_time > response_time_threshold or error_rate > error_rate_threshold:
            print(f"Performance degradation detected during verification. Final stable user count may be lower.")
            final_user_limit = final_user_limit - 1  # Adjust downwards slightly if needed


# Main function to start the test
async def main():
    await intelligent_adjustment()

    if final_user_limit > 0:
        # After fine-tuning, verify the final user limit with multiple attempts
        await verify_max_users()

        print(f"\nFinal validated user count: {final_user_limit}")


# Run the main function with asyncio.run() to handle the event loop correctly
if __name__ == "__main__":
    asyncio.run(main())  # This ensures proper event loop management
