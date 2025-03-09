import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
import io

# 根據專案結構調整下列 import
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

load_dotenv()

async def load_and_merge_data():
    """加載並合併所有產品規格文件"""
    # 讀取hfz.csv
    hfz_df = pd.read_csv("hfz.csv")
    
    # 讀取文字文件並轉換為DataFrame
    def read_txt(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        return pd.read_csv(io.StringIO(content.split("[file content end]")[0]))

    p1_df = read_txt("p1.txt")
    p2_1_df = read_txt("p2-1.txt")
    p2_2_df = read_txt("p2-2.txt")
    
    # 標準化列名並合併數據
    all_data = pd.concat([
        hfz_df.rename(columns={
            "Part Number": "Customer Part Number",
            "Impedance": "Impedance (Ω) at 100 MHz",
            "Rated Current": "Rated Current (mA)"
        }),
        p1_df,
        p2_1_df,
        p2_2_df.rename(columns={
            "Rated Current Lower (mA)": "Rated Current (mA)",
            "Rated Current Upper (mA)": "Rated Current Upper (mA)"
        })
    ], ignore_index=True)
    
    return all_data

async def analyze_chunk(chunk, start_idx, total_records, model_client, termination_condition):
    """分析產品規格批次數據"""
    chunk_data = chunk.to_dict(orient='records')
    prompt = (
        f"正在分析第 {start_idx} 至 {start_idx + len(chunk) - 1} 筆產品規格（共 {total_records} 筆）\n"
        f"規格數據:\n{chunk_data}\n\n"
        "請執行以下任務:\n"
        "1. **產品型號評估**：根據阻抗和額定電流，評估哪些型號最適合高頻應用。\n"
        "2. **合規性檢查**：檢查是否符合 IEC 62368-1 和 ANSI C78.3 標準。\n"
        "3. **異常檢測**：檢測超出標準範圍的值。\n"
        "4. **應用建議**：根據規格，建議適合的應用場景（如無線充電、RF 等）。\n"
        "請各代理人協作完成綜合分析報告。"
    )
    
    # 建立分析團隊
    spec_analyst = AssistantAgent("spec_analyst", model_client,
                                 system_message="您擅長電子元件規格模式識別和趨勢分析")
    
    compliance_checker = AssistantAgent("compliance_checker", model_client,
                                           system_message="專注標準文件檢索和合規性驗證")
    
    application_advisor = AssistantAgent("app_advisor", model_client,
                                        system_message="根據規格推薦適用應用場景")
    anomaly_detector = AssistantAgent("anomaly_detector", model_client,
                                      system_message="檢測超出標準範圍的值")
    
    user_proxy = UserProxyAgent("user_proxy")
    
    analysis_team = RoundRobinGroupChat(
        [spec_analyst, compliance_checker, application_advisor, anomaly_detector, user_proxy],
        termination_condition=termination_condition
    )
    
    messages = []
    async for event in analysis_team.run_stream(task=prompt):
        if isinstance(event, TextMessage):
            print(f"[{event.source}] => {event.content}\n")
            messages.append({
                "batch": f"{start_idx}-{start_idx+len(chunk)-1}",
                "part_numbers": chunk["Customer Part Number"].tolist(),
                "analysis_type": event.source,
                "content": event.content,
                "insight_type": classify_insight(event.content),
                "standards_ref": extract_standards(event.content)
            })
    return messages

def classify_insight(content):
    """分類分析見解類型"""
    if "阻抗" in content and "電流" in content:
        return "參數關係分析"
    elif "標準" in content or "IEC" in content or "ANSI" in content:
        return "合規性分析"
    elif "應用" in content or "場景" in content:
        return "應用建議"
    elif "異常" in content or "超出" in content:
        return "異常檢測"
    return "綜合分析"

def extract_standards(content):
    """提取參考標準"""
    standards = []
    if "IEC" in content:
        standards.extend(["IEC 62368-1", "IEC 60127"])
    if "ANSI" in content:
        standards.append("ANSI C78.3")
    return standards if standards else None

async def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("請檢查 .env 檔案中的 GEMINI_API_KEY")
        return

    model_client = OpenAIChatCompletionClient(
        model="gemini-2.0-flash",
        api_key=gemini_api_key,
    )
    
    termination_condition = TextMentionTermination("分析完成")
    
    # 加載並預處理數據
    full_data = await load_and_merge_data()
    
    # 數據分塊處理
    chunk_size = 50  # 根據規格數據複雜度調整
    chunks = [full_data[i:i+chunk_size] for i in range(0, len(full_data), chunk_size)]
    
    tasks = []
    for idx, chunk in enumerate(chunks):
        tasks.append(analyze_chunk(
            chunk,
            start_idx=idx*chunk_size,
            total_records=len(full_data),
            model_client=model_client,
            termination_condition=termination_condition
        ))
    
    results = await asyncio.gather(*tasks)
    
    # 生成結構化報告
    all_insights = [msg for batch in results for msg in batch]
    report_df = pd.DataFrame(all_insights)
    
    # 保存分析結果
    output_files = {
        "full_analysis.csv": report_df,
        "compliance_issues.csv": report_df[report_df["insight_type"] == "合規性分析"],
        "application_recommendations.csv": report_df[report_df["insight_type"] == "應用建議"]
    }
    
    for filename, df in output_files.items():
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"已生成分析文件: {filename}")

if __name__ == '__main__':
    asyncio.run(main())