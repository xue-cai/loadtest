import logging
import aiohttp
import asyncio
import numpy
import time
from typing import Counter, Dict, Any, List, NamedTuple, Union

logging.basicConfig(level=logging.DEBUG)

class HTTPReponse(NamedTuple):
    status_code: int
    latency: float
    # error: Exception = None

class HTTPLoadTester:
    """
    TODO: A class for performing HTTP load testing and benchmarking.
    """

    def __init__(
        self,
        url: str,
        qps: int = 5,
        duration: int = 10,
        http_method: str = "GET",
        headers: Dict[str, str] = None,
        body: Any = None,
    ) -> None:
        self._url = url
        self._qps = qps
        self._duration = duration
        self._http_method = http_method
        self._headers = headers or {}
        self._body = body

        # stats
        self._responses: List[Union[HTTPReponse, Exception]] = []

    async def run(self) -> None:
        """
        TODO: Runs the load test asynchronously.
        """
        async with aiohttp.ClientSession() as session:
            tasks = []

            start_time = time.time()
            while time.time() - start_time < self._duration:
                task = asyncio.create_task(self._make_request(session))
                tasks.append(task)
                await asyncio.sleep(1 / self._qps)

            await asyncio.gather(*tasks)

            self._print_report()

    async def _make_request(self, session: aiohttp.ClientSession) -> None:
        """
        TODO: Makes a single HTTP request with error handling and latency measurement.
        """
        start = time.time()
        logging.debug(f"making request to {self._url}...")
        try:
            async with session.request(
                self._http_method, self._url, headers=self._headers, data=self._body
            ) as response:
                await response.read()
                self._responses.append(
                    HTTPReponse(
                        status_code=response.status, latency=time.time() - start
                    )
                )
        except aiohttp.ClientError as e:
            # all possible client errors: https://docs.aiohttp.org/en/stable/client_reference.html#hierarchy-of-exceptions
            self._responses.append(e)
        except Exception as e:
            self._responses.append(e)

    def _print_report(self) -> None:
        """
        TODO: Prints the test results including total requests, errors, and average latency.
        """
        total_requests = len(self._responses)
        
        # requests with errors
        error_count = 0
        error_count_by_type = Counter()

        # requests successfully got responses
        response_count = 0
        response_count_success = 0
        response_count_client_error= 0
        response_count_server_error = 0
        response_count_by_status = Counter()
        response_latencies = []
        response_latencies_success = []
        for response in self._responses:
            if isinstance(response, HTTPReponse):
                if response.status_code >= 200 and response.status_code < 400:
                    response_count_success += 1
                    response_latencies_success.append(response.latency)
                elif response.status_code >= 400 and response.status_code < 500:
                    response_count_client_error += 1
                elif response.status_code >= 500 and response.status_code < 600:
                    response_count_server_error += 1
                else:
                    print(f"Error: unknown HTTP status code: {response.status_code}")
                    continue
                response_count += 1
                response_count_by_status[response.status_code] += 1
                response_latencies.append(response.latency)
            else:
                error_count += 1
                error_count_by_type[type(response).__name__] += 1

        print(f"\nTotal requests sent: {total_requests}")
        print(f"  - number of requests got errors: {error_count}")
        print(f"  - number of requests got responses: {response_count}")

        if response_count > 0:
            success_rate = response_count_success / response_count
            average_latency = sum(response_latencies) / response_count
            p50_latency, p75_latency, p95_latency, p99_latency = numpy.percentile(response_latencies, [50, 75, 95, 99])
            print(f"    - success rate: {success_rate*100:.1f}%")
            print(f"    - average latency: {average_latency*1000:.1f}ms")
            print(f"    - p50 latency: {p50_latency*1000:.1f}ms")
            print(f"    - p75 latency: {p75_latency*1000:.1f}ms")
            print(f"    - p95 latency: {p95_latency*1000:.1f}ms")
            print(f"    - p99 latency: {p99_latency*1000:.1f}ms")

            if response_count_success > 0:
                average_latency_success = sum(response_latencies_success) / response_count_success
                p50_latency_success, p75_latency_success, p95_latency_success, p99_latency_success = numpy.percentile(response_latencies_success, [50, 75, 95, 99])
                print(f"    - average latency of success responses: {average_latency_success*1000:.1f}ms")
                print(f"    - p50 latency of success responses: {p50_latency_success*1000:.1f}ms")
                print(f"    - p75 latency of success responses: {p75_latency_success*1000:.1f}ms")
                print(f"    - p95 latency of success responses: {p95_latency_success*1000:.1f}ms")
                print(f"    - p99 latency of success responses: {p99_latency_success*1000:.1f}ms")

        print(f"\n-- More Details --")
        print(f"  - Error count by type: {error_count_by_type}")
        print(f"  - Response count by status code: {response_count_by_status}")
        print("")


async def main():
    load_tester = HTTPLoadTester(
        url="http://www.google.com/xue", duration=2, qps=5
    )  # Set QPS to 5
    await load_tester.run()


asyncio.run(main())
