# LangSmith Tracing Setup for Financial Forecast AI App

Follow these steps to ensure LangSmith tracing works and traces appear in your dashboard:

## 1. Get Your LangSmith API Key
- Go to https://smith.langchain.com/settings
- Copy your API key (starts with `sk-`)

## 2. Create or Update Your `.env` File
- In your project root, create a file named `.env` if it doesn't exist.
- Add the following lines (replace with your actual API key):

```
LANGCHAIN_API_KEY=sk-...your-key-here...
```

## 3. Ensure Environment Variables Are Loaded Early
- Your `financial_agent.py` already loads `.env` and sets:
  - `LANGCHAIN_API_KEY`
  - `LANGCHAIN_TRACING_V2=true`
  - `LANGCHAIN_PROJECT=FinancialForecastAI`
- These must be set **before** any LangChain or LangSmith import.

## 4. Restart Your Terminal and App
- Close all open terminals.
- Open a new terminal in your project root.
- Activate your virtual environment:
  - ` .\.venv\Scripts\Activate.ps1` (PowerShell)
- Run your app:
  - ` .\.venv\Scripts\streamlit.exe run src/ui/app.py --server.port 8570`
  - If port 8570 is busy, use another port (e.g., 8571).

## 5. Confirm Environment Variables Are Set
- When the app starts, you should see:
  - `🔗 LangSmith tracing enabled for project: FinancialForecastAI`
  - `🔑 LANGCHAIN_API_KEY set: yes`
- If you see `no`, check your `.env` file and restart.

## 6. Trigger a Query
- Use the app UI to run a query (any query will do).

## 7. Check Your LangSmith Dashboard
- Go to https://smith.langchain.com/
- Select the `FinancialForecastAI` project.
- You should see traces for your recent runs.

## Troubleshooting
- 401 Unauthorized: Your API key is missing, invalid, or not loaded. Double-check `.env` and restart.
- No traces: Ensure you run a query after startup and that the API key is set.
- Still issues? Print `os.environ` at startup to debug environment variables.

---

**These steps guarantee LangSmith tracing will work if followed exactly.**
