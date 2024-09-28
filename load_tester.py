import gevent
import requests
import time
import logging
from gevent.pool import Pool
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from gevent import monkey

monkey.patch_all()  # Patches standard library to cooperate with gevent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress urllib3 warnings
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Timeout for each request in seconds
REQUEST_TIMEOUT = 30  # Adjusted timeout

# Latency threshold in seconds
LATENCY_THRESHOLD = 5.0  # Adjusted latency threshold

# Number of retries for failed requests
MAX_RETRIES = 3

# Setup session with connection pooling and retry logic
session = requests.Session()
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
session.mount("http://", adapter)
session.mount("https://", adapter)


# Function to send a single HTTP GET request with retries
def ping(url):
    try:
        start_time = time.time()
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        end_time = time.time()
        latency = end_time - start_time
        if response.status_code == 200:
            return True, latency
        else:
            return False, latency
    except requests.RequestException as e:
        logger.debug(f"Request failed: {e}")
        return False, 0


# Function to send multiple requests concurrently
def worker(url, num_requests, results):
    for _ in range(num_requests):
        result = ping(url)
        results.append(result)


# Main function to orchestrate load testing
def load_test(url, initial_requests):
    def perform_test(concurrent_requests):
        pool = Pool(min(concurrent_requests, 100))  # Limit the pool size to prevent overloading
        results = []

        for _ in range(concurrent_requests):
            pool.spawn(worker, url, 1, results)

        pool.join(timeout=REQUEST_TIMEOUT * 2)  # Add timeout to prevent hanging

        success_count = 0
        total_latency = 0
        for success, latency in results:
            if success:
                success_count += 1
                total_latency += latency

        total_requests = concurrent_requests
        avg_latency = total_latency / success_count if success_count else float('inf')
        return success_count, avg_latency

    low = 1
    high = initial_requests
    best = 0
    best_latency = float('inf')
    best_success_count = 0

    # Improved Load Adjustment Logic
    while low <= high:
        mid = (low + high) // 2
        logger.info(f"Testing with {mid} concurrent requests")
        success_count, avg_latency = perform_test(mid)
        success_rate = success_count / mid
        score = success_rate * (LATENCY_THRESHOLD / (avg_latency if avg_latency else 1))
        if success_rate > 0.9 and avg_latency <= LATENCY_THRESHOLD:
            best = mid
            best_latency = avg_latency
            best_success_count = success_count
            low = mid + 1  # Increase load for next test
        else:
            high = mid - 1  # Decrease load for next test
        logger.info(
            f"Concurrent Requests: {mid}, Successes: {success_count}, Average Latency: {avg_latency:.4f} seconds, Score: {score:.4f}")

    # Fine-tune the best value found
    for current_requests in range(best - 5, best + 6):
        if current_requests > 0:
            logger.info(f"Fine-tuning with {current_requests} concurrent requests")
            success_count, avg_latency = perform_test(current_requests)
            success_rate = success_count / current_requests
            score = success_rate * (LATENCY_THRESHOLD / (avg_latency if avg_latency else 1))
            if success_rate > 0.9 and avg_latency <= LATENCY_THRESHOLD:
                best = current_requests
                best_latency = avg_latency
                best_success_count = success_count
            logger.info(
                f"Concurrent Requests: {current_requests}, Successes: {success_count}, Average Latency: {avg_latency:.4f} seconds, Score: {score:.4f}")

    logger.info(f"Initial Maximum concurrent requests the website can handle: {best}")
    logger.info(
        f"Initial Best Success Count: {best_success_count}, Initial Best Average Latency: {best_latency:.4f} seconds")

    # Exploratory phase to ensure the maximum capacity
    final_max = best
    step = 500  # Start with a larger step
    current_requests = best + step
    previous_latency = best_latency
    multiplier = 1.5  # Exponential step size increase factor

    while True:
        logger.info(f"Exploratory phase with {current_requests} concurrent requests")
        success_count, avg_latency = perform_test(current_requests)
        success_rate = success_count / current_requests
        if success_rate > 0.9 and avg_latency <= LATENCY_THRESHOLD:
            final_max = current_requests
            if avg_latency < previous_latency * 1.2:  # Increase step if latency increase is within 20%
                step = int(step * multiplier)
            else:  # Decrease step if latency increases significantly
                step = max(step // 2, 100)
            previous_latency = avg_latency
            current_requests += step
        else:
            break
        logger.info(
            f"Concurrent Requests: {current_requests}, Successes: {success_count}, Average Latency: {avg_latency:.4f} seconds")

    logger.info(f"Final Maximum concurrent requests the website can handle: {final_max}")


if __name__ == '__main__':
    # main function for quick testing of functionality
    url = 'https://hogar.aiems.ae'  # Replace with the target URL
    initial_requests = 500  # Start with a larger number of concurrent requests
    load_test(url, initial_requests)
