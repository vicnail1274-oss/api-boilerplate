# AT-009：升級 `unified_kb` 為 Knowledge Graph（含 LLM Wiki 替代 RAG）設計文件

## 1. 任務背景與目標

Webhook 指示目標：

1. 研究 LLM Wiki + Knowledge Graph（取代傳統 RAG）
2. 評估 `unified_kb.json` 從 flat 結構升級為 graph 的工作量
3. 設計 AI Council 的圖譜化決策機制
4. 將設計輸出到 `output/`

> 本文件優先滿足 DoD：**完成「LLM Wiki + Knowledge Graph（取代 RAG）」研究整理**，並一併提供可落地的升級設計。

---

## 2. 研究摘要：LLM Wiki + Knowledge Graph 為何能取代（或大幅弱化）Baseline RAG

### 2.1 參考脈絡（外部）

- Microsoft GraphRAG 文件與研究（From Local to Global, 2024）
  - 核心：先從文本抽取實體/關係形成知識圖，再以社群摘要（community summaries）支援查詢。
- LLM Wiki（Karpathy 概念的開源實作）
  - 核心：把「知識維護」拆成三層：Raw Sources、Wiki（LLM 維護）、Schema（規則）。
  - 重點不是即時 chunk 檢索，而是持續編譯、重整、交叉引用。

### 2.2 Baseline RAG 的限制

傳統向量 RAG（top-k chunks）常見問題：

1. **缺少關係語意**：chunk 與 chunk 之間無顯式關聯，跨文件多跳推理較弱。  
2. **全域問題表現差**：例如「這個領域的主要趨勢」需要彙整，而非單次相似度檢索。  
3. **可追溯性有限**：很難清楚呈現「答案依賴哪些節點與關係」。  
4. **知識治理困難**：更新時常發生重複 chunk、衝突陳述、漂移與過期內容。

### 2.3 LLM Wiki + Graph 的優勢

1. **知識先編譯（compile-time synthesis）**  
   將原始來源轉成結構化 wiki + graph，不是每次 query 才臨時拼接片段。  
2. **多跳與關聯推理**  
   透過節點與邊可自然支援「A 影響 B，B 約束 C」等推理。  
3. **全域與局部雙模式**  
   - 全域：社群摘要/主題節點回答趨勢型問題  
   - 局部：近鄰擴展回答實體型問題  
4. **可治理、可審計**  
   可為每個節點/邊附來源、信心分數、更新時間、衝突標記。  
5. **更符合 AI Council 協作**  
   多代理可對同一圖譜子圖辯論，並留下決策與證據鏈。

### 2.4 結論（研究面）

對「需要長期累積、跨來源整合、可追溯」的任務，**Graph-first + Wiki-first** 方案可作為主體架構；向量檢索可降級為輔助（fallback 或召回補充），而非核心真相來源。

---

## 3. 目標架構（Target Architecture）

## 3.1 三層知識架構

1. **Raw Layer（不可變原始層）**
   - 原始文件、會議記錄、規格、外部研究
   - 僅追加、不覆寫

2. **Wiki Layer（LLM 維護語義層）**
   - 主題頁、實體頁、決策頁、爭議頁
   - 每頁必帶來源 references 與版本

3. **Graph Layer（可查詢推理層）**
   - Nodes：Entity / Concept / Decision / Evidence / Task / Constraint
   - Edges：supports / contradicts / depends_on / owned_by / impacts / derived_from
   - Node/Edge 屬性：`confidence`, `source_ids`, `last_verified_at`, `status`

## 3.2 查詢流程（替代純 RAG）

1. Query 理解與意圖分類（全域/局部/決策型）  
2. 先走 Graph 檢索（子圖擷取、路徑搜尋、社群摘要）  
3. 再走 Wiki 組裝（引用頁面摘要與來源）  
4. 只有證據不足時才觸發 vector fallback  
5. 生成答案時附上：
   - 主要依據節點/邊
   - 衝突觀點
   - 信心與待驗證項

---

## 4. `unified_kb.json` 升級評估：Flat -> Graph

## 4.1 假設目前 flat 結構特徵

即使未提供實際檔案，flat `unified_kb.json` 常見型態通常包含：

- 以條目（records/items）為主，欄位類似 `title`, `content`, `tags`, `source`
- 缺少明確關係（relation）欄位，或只有弱連結（tag/string）
- 缺少版本、信心、衝突與證據鏈

## 4.2 目標 graph schema（建議）

```json
{
  "nodes": [
    {
      "id": "concept:retrieval_augmented_generation",
      "type": "Concept",
      "name": "Retrieval-Augmented Generation",
      "summary": "...",
      "source_ids": ["src:paper_2404_16130"],
      "confidence": 0.87,
      "last_verified_at": "2026-04-08T00:00:00Z",
      "status": "active"
    }
  ],
  "edges": [
    {
      "id": "edge:graphrag_addresses_rag_global_q",
      "type": "addresses",
      "from": "concept:graphrag",
      "to": "problem:global_query_failure",
      "source_ids": ["src:paper_2404_16130"],
      "confidence": 0.83
    }
  ],
  "sources": [
    {
      "id": "src:paper_2404_16130",
      "kind": "paper",
      "title": "From Local to Global",
      "url": "https://arxiv.org/abs/2404.16130"
    }
  ]
}
```

## 4.3 遷移策略

1. **欄位正規化**：先把 flat records 轉成 canonical objects。  
2. **實體抽取**：由規則 + LLM 抽取 Entity/Concept。  
3. **關係抽取**：建立 `supports/contradicts/depends_on/...` 邊。  
4. **去重與同義合併**：處理 alias、同名不同義。  
5. **來源綁定**：每個 node/edge 綁 `source_ids`。  
6. **信心分數與人工覆核機制**：低分先進待審。  
7. **增量更新管線**：新資料只重算受影響子圖。

## 4.4 工作量拆解（技術複雜度）

### A. 資料模型與儲存（中）
- 定義 node/edge/source schema
- 加入版本與狀態欄位

### B. ETL/抽取管線（中到高）
- 實體/關係抽取品質是核心風險
- 需加入去重、衝突檢測、重試機制

### C. 查詢層重構（中）
- 由 `chunk retrieval` 改為 `subgraph retrieval`
- 需支援全域摘要 + 局部推理

### D. 治理與觀測（中）
- 指標：覆蓋率、衝突率、答案可追溯率、人工覆核通過率

### E. 與現有流程相容（中）
- 保留向量 fallback，降低切換風險

整體屬於**架構升級型改造**，不是單點修補；最關鍵難點是「關係抽取品質」與「持續治理」。

---

## 5. AI Council 圖譜化決策設計

## 5.1 角色模型（示例）

- **Planner Agent**：拆解目標、定義決策節點
- **Research Agent**：補證據與來源
- **Skeptic Agent**：尋找反例與矛盾
- **Risk Agent**：評估風險與依賴
- **Judge Agent**：整合投票與輸出決議

## 5.2 決策圖譜資料模型

- `Decision` 節點：候選方案、狀態（proposed/accepted/rejected）
- `Evidence` 節點：支援或反對證據
- `Constraint` 節點：成本、法規、時序、資源
- `AgentOpinion` 節點：代理人觀點與信心
- 關係：
  - `supports` / `contradicts`
  - `constrained_by`
  - `proposed_by`
  - `supersedes`（新決策取代舊決策）

## 5.3 決策流程

1. 建立 `Decision` 候選集合  
2. 各 agent 對候選方案掛載 `Evidence` 與 `AgentOpinion`  
3. Judge 依規則聚合：
   - 證據覆蓋度
   - 衝突強度
   - 約束可行性
   - 信心加權分數
4. 產生決議與「可追溯決策鏈」
5. 將結果寫回 Wiki + Graph 作為後續任務依據

## 5.4 最小可行決策規則（MVP）

- 決策接受門檻：
  - `support_score - contradict_score >= threshold`
  - 必要約束全部滿足
  - 至少一個高可信來源
- 若未達門檻：標記 `needs_more_evidence`

---

## 6. 實作路線建議（由低風險到高能力）

## Phase 1：Graph 基礎化
- 定義 schema
- 將現有 `unified_kb` 匯入 nodes/sources（先不做複雜關係）
- 提供基本 query API（node lookup, neighborhood）

## Phase 2：關係抽取與治理
- 加入 LLM relation extraction
- 去重、別名合併、衝突標記
- 人工覆核後回寫（human-in-the-loop）

## Phase 3：Graph-based QA
- 實作 global/local 決策型查詢路徑
- 將向量檢索改為 fallback
- 回答附上決策鏈與來源鏈

## Phase 4：AI Council 決策自動化
- 代理人意見入圖
- 規則化投票與決議輸出
- 自動生成決策頁（wiki）

---

## 7. 風險與對策

1. **關係抽取錯誤率高**  
   - 對策：低信心關係進待審池；重要邊要求多來源一致。

2. **圖譜膨脹與查詢成本增加**  
   - 對策：社群摘要、子圖快取、冷資料分層存放。

3. **舊流程切換風險**  
   - 對策：雙軌期保留 baseline RAG fallback。

4. **治理不足導致知識腐化**  
   - 對策：建立 lint/health check（孤兒節點、過期證據、衝突未解）。

---

## 8. 驗收建議（可用於後續工作單）

1. 可從 `unified_kb` 匯出 graph JSON（nodes/edges/sources）  
2. 查詢可返回「答案 + 子圖證據 + 來源」  
3. 支援至少一個全域問題與一個多跳問題，且可追溯  
4. AI Council 可對同一決策輸出：
   - 支持與反對證據
   - 最終決議與理由
   - `needs_more_evidence` 分支

---

## 9. 本次 webhook 產出對照

- [x] 研究 LLM Wiki + Knowledge Graph approach（取代/弱化傳統 RAG）
- [x] 評估 `unified_kb.json` flat -> graph 的升級工作
- [x] 設計 AI Council graph-based decision making
- [x] 設計文件寫入 `output/`

