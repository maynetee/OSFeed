export default function Settings() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Settings</h2>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Configuration</h3>

          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Environment Variables</h4>
              <p className="text-sm text-gray-500 mb-4">
                Settings are configured via environment variables in the .env file.
              </p>

              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Preferred Language:</span>
                  <span className="text-sm text-gray-900">
                    Set via PREFERRED_LANGUAGE in .env
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Summary Time:</span>
                  <span className="text-sm text-gray-900">Set via SUMMARY_TIME in .env</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Translation Service:</span>
                  <span className="text-sm text-gray-900">OpenAI (model configurable in .env)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">LLM Service:</span>
                  <span className="text-sm text-gray-900">
                    OpenAI (model configurable in .env)
                  </span>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Background Jobs</h4>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Message Collection:</span>
                  <span className="text-sm text-gray-900">Every 2 minutes</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">Daily Summary:</span>
                  <span className="text-sm text-gray-900">
                    Configured time (check .env)
                  </span>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">API Information</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">
                  API documentation is available at:{' '}
                  <a
                    href="http://localhost:8000/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    http://localhost:8000/docs
                  </a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Setup Instructions</h4>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Copy .env.example to .env and fill in your API credentials</li>
          <li>Get Telegram API credentials from https://my.telegram.org/apps</li>
          <li>Get OpenRouter API key from https://openrouter.ai</li>
          <li>Run docker-compose up to start all services</li>
          <li>Add channels via the Channels page</li>
          <li>Wait for messages to be collected (every 5 minutes)</li>
          <li>Generate summaries from the Dashboard</li>
        </ol>
      </div>
    </div>
  )
}
