# 語音聲學資料初探分析儀表板

本專案是一個使用 **Streamlit** 建立的語音聲學資料初探分析儀表板，主要用於整合資料預覽、資料品質檢查、互動式視覺化、批次混合效應模型分析，以及結果匯出流程。

由於原始研究／計畫資料涉及保密，無法公開於 GitHub，因此本專案使用模擬資料（fake data）重現語音聲學資料的結構與分析流程。此專案的重點不在於解釋模擬資料本身的統計結果，而是展示如何將語音資料分析流程整理成可操作、可重複使用的互動式工具。

---

## 專案動機

語音聲學資料分析通常會涉及許多重複性工作，例如：

- 檢查資料欄位與資料型態
- 確認缺失值與異常值
- 比較不同條件下的聲學特徵差異
- 繪製探索性圖表
- 對多個聲學特徵批次執行統計模型
- 匯出分析結果與圖表

若每次分析都以手動方式撰寫程式，容易造成流程分散、重複操作，也不利於後續檢查與展示。因此，本專案嘗試將語音聲學資料的初步分析流程整合為一個互動式儀表板，讓使用者可以透過介面快速進行資料探索與統計建模。

---

## 專案定位

本專案定位為：

> 使用模擬資料展示一個語音聲學資料的初探分析流程，包含資料檢查、互動式視覺化、批次 MixedLM 統計建模與結果匯出。

需要特別說明的是：

- 本專案沒有公開真實研究資料。
- 模擬資料僅用於展示 dashboard 的功能與分析流程。
- 模擬資料產生的統計結果不代表任何真實研究發現。
- 本專案重點是資料分析流程設計、互動式介面設計與程式模組化。

---

## 主要功能

### 1. 資料上傳與預覽

儀表板支援上傳以下格式的資料：

- CSV
- Excel（`.xlsx`, `.xls`）

若使用者沒有上傳資料，系統會自動產生一份模擬語音聲學資料作為展示。

模擬資料包含的欄位例如：

- `speaker_id`
- `word_id`
- `condition`
- `register`
- `group`
- `scale_score`
- `duration_ms`
- `f0_mean`
- `intensity_db`

這些欄位用來模擬語音分析中常見的受試者、詞項、實驗條件、語域、組別、量表分數與聲學特徵。

---

### 2. 資料品質檢查

在 Overview 頁面中，使用者可以檢查目前資料的基本狀況，包括：

- 資料預覽
- 欄位型態
- 各欄位的獨立值數量
- 缺失值數量
- 缺失值比例
- 數值欄位中的 `-1` 數量

其中 `-1` 檢查是為了模擬某些研究資料中可能會使用特定數值表示缺失值或異常值的情況。使用者可以藉此快速判斷資料是否需要進一步清理。

---

### 3. 全域篩選

儀表板左側提供全域篩選功能。

系統會自動偵測適合篩選的欄位，例如類別欄位或獨立值數量不太高的欄位，讓使用者可以依照條件篩選資料，例如：

- 特定 speaker
- 特定 word
- 特定 condition
- 特定 register
- 特定 group

篩選後的資料會同步影響 Overview、Explore Visualization 與 Batch MixedLM 頁面。

---

### 4. 互動式探索性視覺化

Explore Visualization 頁面提供互動式圖表選擇，使用者可以自由指定：

- X 軸變項
- Y 軸聲學特徵
- hue 分組變項
- 圖表類型

目前支援的圖表類型包括：

- Boxplot
- Violin plot
- Barplot
- Lineplot
- Scatterplot

此頁面也會根據使用者選擇的 X、Y 與 hue 產生摘要統計表，包含：

- N
- Mean
- Standard Deviation
- Median
- Minimum
- Maximum

同時，系統會產生簡短的自動觀察文字，協助使用者快速掌握目前圖表中平均值最高與最低的群組。

---

### 5. 批次 MixedLM 統計分析

Batch MixedLM 頁面提供批次混合效應模型分析功能。使用者可以一次選擇多個聲學特徵作為 outcome，並套用相同的模型設定。

使用者可以指定：

- 多個 Y 變項，也就是 acoustic outcomes
- 一個 fixed effect
- 一個 random intercept
- 一個可選的 moderator
- fixed effect 要視為連續變項、類別變項，或由系統自動判斷

模型形式例如：

```text
outcome ~ fixed_effect + (1 | random_intercept)
```

若加入 moderator，則模型形式為：

```text
outcome ~ fixed_effect * moderator + (1 | random_intercept)
```

模型結果會整理成表格，包含：

- outcome
- formula
- term
- effect type
- coefficient
- standard error
- z-value
- p-value
- AIC
- BIC
- convergence status
- observations
- number of random-effect groups

---

### 6. 交互作用與趨勢圖

當使用者選擇 moderator 時，系統會依據 fixed effect 的型態自動產生適合的圖表。

若 fixed effect 被視為連續變項或量表變項，系統會產生：

- Plotly regression trend plot
- 不同 moderator 條件下的斜率趨勢圖

若 fixed effect 被視為類別變項，系統會產生：

- grouped mean plot
- interaction profile plot

這些圖表可協助使用者在解讀統計模型前後，進一步觀察不同條件下的資料趨勢與交互作用模式。

---

### 7. 結果匯出

本專案支援匯出分析結果，包含：

- MixedLM 結果 Excel 檔
- 單張 Plotly 圖表 HTML 檔
- 多張交互作用圖或趨勢圖 ZIP 檔

這讓分析結果可以被保存、分享，或進一步放入報告與作品集中。

---

## 專案結構

```text
speech_acoustic_dashboard/
│
├── app.py              # Streamlit 主程式入口
├── data_utils.py       # 資料讀取、模擬資料產生、欄位偵測
├── plot_utils.py       # 摘要表與 Plotly 視覺化函式
├── model_utils.py      # MixedLM 統計模型相關函式
├── export_utils.py     # Excel、HTML、ZIP 匯出函式
├── ui_helpers.py       # 側邊欄篩選與 UI 輔助函式
├── ui_sections.py      # 各個 Streamlit tab 的畫面渲染
│
├── requirements.txt
└── README.md
```

此結構將資料處理、視覺化、統計建模、匯出與 UI 畫面分開，讓專案較容易維護，也更接近正式資料分析專案的組織方式。

---

## 安裝與執行方式

### 1. 下載專案

```bash
git clone <your-repository-url>
cd speech_acoustic_dashboard
```

### 2. 建立虛擬環境

```bash
python -m venv venv
```

macOS / Linux：

```bash
source venv/bin/activate
```

Windows：

```bash
venv\Scripts\activate
```

### 3. 安裝套件

```bash
pip install -r requirements.txt
```

### 4. 執行 Streamlit app

```bash
streamlit run app.py
```

---

## requirements.txt

本專案主要使用以下 Python 套件：

```text
streamlit>=1.35.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.20.0
statsmodels>=0.14.0
openpyxl>=3.1.0
```

---

## 使用情境範例

此 dashboard 可作為語音聲學資料初探分析工具。

例如，研究者可能想初步檢查：

- 不同 condition 下的音長是否有差異
- 不同 register 下的 intensity 是否不同
- scale score 是否與 duration 或 F0 有趨勢關係
- speaker 或 word 的隨機差異是否需要被控制
- 多個聲學特徵是否可以用同一組模型設定批次分析

透過此儀表板，使用者可以依序完成：

1. 上傳或載入資料
2. 檢查資料品質
3. 套用全域篩選
4. 進行探索性視覺化
5. 批次執行 MixedLM
6. 匯出模型結果與圖表

---

## 保密資料與模擬資料說明

由於原始研究／計畫資料涉及保密，無法公開於此 repository。

為了讓專案可以公開展示，本專案使用模擬資料重現語音聲學資料分析的情境。模擬資料的目的包括：

- 展示 dashboard 的操作流程
- 展示資料檢查與視覺化功能
- 展示批次 MixedLM 分析邏輯
- 展示結果匯出流程
- 讓專案可以被他人下載與執行

因此，模擬資料產生的統計結果不應被視為真實研究結論。

---

## 展示能力

此專案展示了以下能力：

- Python 資料分析
- Streamlit 互動式儀表板開發
- pandas 資料處理與摘要統計
- Plotly 互動式視覺化
- statsmodels MixedLM 統計建模
- 批次分析流程自動化
- 資料品質檢查流程設計
- 模組化 Python 專案結構
- 分析結果匯出與報告支援

---

## 後續可擴充方向

未來可進一步擴充：

- 支援 random slopes
- 支援三階交互作用
- 支援使用者自訂 formula
- 加入 estimated marginal means
- 加入 simple effects analysis
- 加入 full model 與 reduced model 比較
- 加入自動分析報告產生
- 加入更彈性的缺失值處理設定
- 加入圖表主題與配色設定
- 加入真實資料格式的欄位對應設定

---

## 專案限制

目前版本仍屬於初探分析工具，主要限制包括：

- 尚未支援 random slopes
- 尚未支援複雜模型比較流程
- 尚未支援 estimated marginal means
- 尚未支援完整的統計報告自動生成
- 模擬資料不代表真實研究結果

因此，本專案較適合作為探索性分析、流程展示與作品集專案，而非直接取代正式研究分析流程。

---

## 作者說明

本專案源於語音聲學資料分析與研究流程整理的需求，目標是將重複性的資料檢查、視覺化與統計建模步驟整合為互動式工具，提升分析流程的可讀性、可操作性與可重複性。


## 線上展示

本專案已部署於 Streamlit Community Cloud，可直接透過以下連結操作儀表板：
[開啟 Dashboard](https://speech-acoustic-dashboard-claire-project.streamlit.app/)
