from prometheus_client import Counter, Gauge, Histogram

JOB_DURATION = Histogram(
    "osfeed_job_duration_seconds",
    "Duration of background jobs",
    ["job_name"],
)
JOB_SUCCESS = Counter(
    "osfeed_job_success_total",
    "Total successful job executions",
    ["job_name"],
)
JOB_FAILURE = Counter(
    "osfeed_job_failure_total",
    "Total failed job executions",
    ["job_name"],
)
TRANSLATION_QUEUE_SIZE = Gauge(
    "osfeed_translation_queue_size",
    "Number of messages pending translation",
)
DLQ_SIZE = Gauge(
    "osfeed_dlq_size",
    "Number of entries in dead letter queue",
)
