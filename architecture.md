
# 🏗️ The System Architecture

```mermaid
graph TD
    subgraph "1. Data Sources (The Raw Material)"
        YF[Yahoo Finance API] -->|Prices, Volume, News| T_Agent
        YF -->|News Headlines| S_Agent
        SEC[SEC EDGAR API] -->|10-K/10-Q Filings| F_Agent
        Wiki[Wikipedia / Static List] -->|Euro Tickers| T_Agent
    end

    subgraph "2. The AI Agents (Processing Layer)"
        T_Agent[Technical Agent] -->|Calculates Williams %R & RSI| DB
        F_Agent[Fundamental Agent] -->|Calculates Current Ratio, FCF| DB
        S_Agent[Sentiment Agent] -->|Scores News Polarity| DB
        Info_Agent[Info Agent] -->|Fetches ISIN & Names| DB
    end

    subgraph "3. The Brain (Storage)"
        DB[(SQLite Database)]
        DB -->|Stores| Table_Tech[Technical Analysis Table]
        DB -->|Stores| Table_Fund[Fundamental Analysis Table]
        DB -->|Stores| Table_Sent[Sentiment Analysis Table]
        DB -->|Stores| Table_Info[Stock Info Table]
    end

    subgraph "4. The Interface (Delivery)"
        Table_Tech -->|Query| Dashboard[Interactive Dashboard (Colab)]
        Table_Fund -->|Query| Dashboard
        Table_Sent -->|Query| Dashboard
        Table_Tech & Table_Fund & Table_Sent -->|Export| CSV[Final_CSV_Report.csv]
        CSV -->|Feed| MCP[Future MCP Agents]
    end

    style DB fill:#f9f,stroke:#333,stroke-width:2px
    style Dashboard fill:#bbf,stroke:#333,stroke-width:2px
    style CSV fill:#bfb,stroke:#333,stroke-width:2px
```
