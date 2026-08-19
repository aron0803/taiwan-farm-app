"""
建立/重建作物資料庫 (SQLite)。
每筆栽培/病蟲害資料都必須附 source_url + source_type + fetched_date，
沒有可靠來源的內容一律放進 unverified_notes，不進正式資料表。

source_type:
  official - 政府機關(改良場/農業部)發布的正式文章或研究資料
  qa       - 農業知識入口網的使用者問答/論壇內容，可信度較低，上線前需人工複核
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "crops.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS crop_registry (
    crop_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('collected','pending'))
);

CREATE TABLE IF NOT EXISTS crops (
    crop_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    region_north TEXT,
    region_central TEXT,
    region_south TEXT,
    region_note TEXT,
    season_months_north TEXT,   -- 逗號分隔月份數字(1-12)，NULL表示原文未給出明確月份，不列入「現在適合種」篩選
    season_months_central TEXT,
    season_months_south TEXT,
    season_label TEXT NOT NULL  -- 人類可讀的季節描述，永遠要有值，即使月份未知
);

CREATE TABLE IF NOT EXISTS cultivation_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id),
    field TEXT NOT NULL,
    value TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('official','qa')),
    fetched_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    symptom TEXT NOT NULL,
    control TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('official','qa')),
    fetched_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unverified_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_id TEXT NOT NULL REFERENCES crops(crop_id),
    note TEXT NOT NULL
);
"""

# 蒐集路線圖：依食用部位分類（葉菜/花菜/根莖/果菜/豆菜/果樹/雜糧），
# 涵蓋台灣常見作物，先列出骨架，狀態隨蒐集進度更新。
REGISTRY = [
    # 葉菜類
    ("xiaobaicai", "小白菜", "葉菜類", "collected"),
    ("digualve", "地瓜葉", "葉菜類", "collected"),
    ("kongxincai", "空心菜", "葉菜類", "collected"),
    ("bocai", "菠菜", "葉菜類", "collected"),
    ("tongao", "茼蒿", "葉菜類", "collected"),
    ("jielan", "芥藍", "葉菜類", "collected"),
    ("gaolicai", "高麗菜", "葉菜類", "collected"),
    ("dabaicai", "大白菜", "葉菜類", "collected"),
    ("azhai", "A菜（萵苣）", "葉菜類", "collected"),
    # 花菜類
    ("huaqielan", "花椰菜", "花菜類", "collected"),
    ("lvhuaqielan", "青花菜（綠花椰）", "花菜類", "collected"),
    # 根莖類
    ("luobo", "蘿蔔", "根莖類", "collected"),
    ("huluobo", "胡蘿蔔", "根莖類", "collected"),
    ("malingshu", "馬鈴薯", "根莖類", "collected"),
    ("yutou", "芋頭", "根莖類", "collected"),
    ("jiang", "薑", "根莖類", "collected"),
    ("yangcong", "洋蔥", "根莖類", "collected"),
    # 果菜類
    ("fanqie", "番茄（小果）", "果菜類", "collected"),
    ("qiezi", "茄子", "果菜類", "collected"),
    ("tianjiao", "甜椒", "果菜類", "collected"),
    ("xiaohuanggua", "小黃瓜", "果菜類", "collected"),
    ("sigua", "絲瓜", "果菜類", "collected"),
    ("donggua", "冬瓜", "果菜類", "collected"),
    ("nangua", "南瓜", "果菜類", "collected"),
    ("kugua", "苦瓜", "果菜類", "collected"),
    # 豆菜類
    ("sijidou", "四季豆", "豆菜類", "collected"),
    ("wandou", "豌豆", "豆菜類", "collected"),
    ("maodou", "毛豆", "豆菜類", "collected"),
    # 果樹
    ("bale", "芭樂", "果樹", "collected"),
    ("ganju", "柑橘", "果樹", "collected"),
    ("xiangjiao", "香蕉", "果樹", "collected"),
    ("mangguo", "芒果", "果樹", "collected"),
    ("mugua", "木瓜", "果樹", "collected"),
    ("fengli", "鳳梨", "果樹", "collected"),
    ("lianwu", "蓮霧", "果樹", "collected"),
    # 雜糧
    ("yumi", "玉米", "雜糧", "collected"),
    ("digua", "地瓜（甘藷塊根）", "雜糧", "collected"),
    # 蔥蒜類（新增分類）
    ("jiucai", "韭菜", "蔥蒜類", "collected"),
    ("cong", "蔥", "蔥蒜類", "collected"),
    ("dasuan", "大蒜", "蔥蒜類", "collected"),
    # 果菜類（新增）
    ("xigua", "西瓜", "果菜類", "collected"),
    # 葉菜類/雜糧（新增）
    ("jiecai", "芥菜", "葉菜類", "collected"),
    ("youcai", "油菜", "雜糧", "collected"),
    # 果樹（新增）
    ("lizhi", "荔枝", "果樹", "collected"),
    ("longyan", "龍眼", "果樹", "collected"),
    ("baixiangguo", "百香果", "果樹", "collected"),
    ("huolongguo", "火龍果", "果樹", "collected"),
    # 根莖類（新增）
    ("shanyao", "山藥", "根莖類", "collected"),
    ("niupang", "牛蒡", "根莖類", "collected"),
    ("lusun", "蘆筍", "根莖類", "collected"),
    ("jiaobaisun", "茭白筍", "根莖類", "collected"),
    # 豆菜類/雜糧（新增）
    ("hongdou", "紅豆", "豆菜類", "collected"),
    ("huasheng", "花生", "雜糧", "collected"),
    # 果樹（新增）
    ("putao", "葡萄", "果樹", "collected"),
    ("caomei", "草莓", "果樹", "collected"),
    # 果菜類/葉菜類/根莖類（新增）
    ("qiukui", "秋葵", "果菜類", "collected"),
    ("huanggongcai", "皇宮菜（落葵）", "葉菜類", "collected"),
    ("jiucengta", "九層塔", "葉菜類", "collected"),
    ("xiangcai", "香菜（芫荽）", "葉菜類", "collected"),
    ("lianou", "蓮藕", "根莖類", "collected"),
    # 果樹（新增）
    ("yangtao", "楊桃", "果樹", "collected"),
    ("shijia", "釋迦", "果樹", "collected"),
    ("tianshi", "甜柿", "果樹", "collected"),
    # 果菜類/葉菜類/根莖類（新增）
    ("yangxiangua", "洋香瓜（哈密瓜／香瓜）", "果菜類", "collected"),
    ("longxucai", "龍鬚菜", "葉菜類", "collected"),
    ("shansu", "山蘇", "葉菜類", "collected"),
    ("guomao", "過貓（過溝菜蕨）", "葉菜類", "collected"),
    ("tiancaigen", "甜菜根", "根莖類", "collected"),
    ("biqi", "荸薺（馬蹄）", "根莖類", "collected"),
    # 果樹/雜糧/特用作物（新增，來自fae.moa.gov.tw縣市農產地圖）
    ("pingguo", "蘋果", "果樹", "collected"),
    ("pipa", "枇杷", "果樹", "collected"),
    ("hongzao", "紅棗", "果樹", "collected"),
    ("laoli", "酪梨", "果樹", "collected"),
    ("dadou", "大豆（黃豆）", "雜糧", "collected"),
    ("jinzhen", "金針", "特用作物", "collected"),
    ("xiancao", "仙草", "特用作物", "collected"),
    ("luoshenkui", "洛神葵", "特用作物", "collected"),
    # 特用作物/雜糧/豆菜類/根莖類/果樹/蔥蒜類（新增，來自fae.moa.gov.tw縣市農產地圖第二批）
    ("kafei", "咖啡", "特用作物", "collected"),
    ("lingjiao", "菱角", "根莖類", "collected"),
    ("yelian", "野蓮", "葉菜類", "collected"),
    ("shudou", "樹豆", "豆菜類", "collected"),
    ("taiwanli", "台灣藜", "特用作物", "collected"),
    ("xiaomi", "小米", "雜糧", "collected"),
    ("ningmeng", "檸檬", "果樹", "collected"),
    ("hongcongtou", "紅蔥頭", "蔥蒜類", "collected"),
    # 第三批（來自農業部「地方特色作物」官方清單）
    ("lajiao", "辣椒", "果菜類", "collected"),
    ("qingjiangcai", "青江菜", "葉菜類", "collected"),
    ("qincai", "芹菜", "葉菜類", "collected"),
    ("bianbu", "扁蒲（蒲瓜）", "果菜類", "collected"),
    ("hugua", "胡瓜（花胡瓜）", "果菜類", "collected"),
    ("jianghuang", "薑黃", "根莖類", "collected"),
    ("lanmei", "藍莓", "果樹", "collected"),
    ("huangdidou", "皇帝豆（萊豆）", "豆菜類", "collected"),
    # 第四批（來自農業部「地方特色作物」官方清單）
    ("qiujingganlan", "球莖甘藍（結頭菜）", "根莖類", "collected"),
    ("yuegua", "越瓜（醃瓜）", "果菜類", "collected"),
    ("jiangdou", "豇豆（長豆）", "豆菜類", "collected"),
    ("midou", "米豆", "豆菜類", "collected"),
    ("ganzhe", "甘蔗", "雜糧", "collected"),
    ("huma", "胡麻（芝麻）", "雜糧", "collected"),
    ("hangju", "杭菊", "特用作物", "collected"),
]

def M(*months):
    """月份清單轉逗號分隔字串；不傳參數代表原文未給出明確月份。"""
    return ",".join(str(m) for m in months) if months else None


ALL_YEAR = M(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

CROPS = [
    dict(crop_id="xiaobaicai", name="小白菜", category="葉菜類",
         region_north="四季皆可，夏季以設施栽培為主（颱風、豪雨後復耕作物）",
         region_central="四季皆可，春秋為主要產季",
         region_south="四季皆可，高溫期須留意軟腐病與蟲害壓力較大",
         region_note="生育期短、耐候範圍廣，北中南皆可栽種；地區差異主要在盛產季節與病蟲害壓力，而非能否種植。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="四季皆可栽種，以春、秋兩季為佳"),
    dict(crop_id="digualve", name="地瓜葉", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得官方分區資料，僅取得插枝法通用種植資訊，地區差異待補查。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="尚無官方季節資料（僅查得使用者問答等級的扦插種植方式）"),
    dict(crop_id="fanqie", name="番茄（小果）", category="果菜類",
         region_north="秋冬作低溫多濕不適宜，春、夏作可種植",
         region_central="全年均可種植",
         region_south="全年均可種植",
         region_note="官方資料明確標示北部與中南部的可種植季節不同，是三個作物中地區差異最明確的一筆。",
         season_months_north=M(3, 4, 5, 6, 7, 8), season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="北部春夏作（秋冬低溫多濕不宜），中南部全年可種植"),
    dict(crop_id="kongxincai", name="空心菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="官方資料強調「台灣全年皆可栽培」，未特別區分北中南差異，推測因其耐熱耐濕特性對氣候不敏感。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="耐熱喜濕，台灣全年皆可栽培"),
    dict(crop_id="luobo", name="蘿蔔", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="盛產期為12月至翌年初春（秋冬蘿蔔），尚未取得北中南分區資料。栽培數據來源含中國大陸農業網站，單位使用「畝」「釐米」，套用到台灣前需換算並與台灣本地資料交叉驗證。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="秋冬蘿蔔，盛產12月至翌年初春；原文未給出明確播種月份，暫不列入「現在適合種」篩選"),
    dict(crop_id="gaolicai", name="高麗菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="官方資料區分夏播（高冷地7～9月）與秋播（平地9～11月）兩套栽培期，暗示高溫地區需仰賴高冷地（多在中部山區）夏季供應，尚未取得明確北中南分區敘述。",
         season_months_north=M(3, 4, 9, 10, 11), season_months_central=M(3, 4, 7, 8, 9, 10, 11), season_months_south=M(3, 4, 9, 10, 11),
         season_label="夏播3～4月，秋播高冷地7～9月／平地9～11月；北部與南部平地不具高冷地優勢，暫排除7～8月高冷地夏播窗口"),
    dict(crop_id="dabaicai", name="大白菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，且本次查得的栽培細節多來自使用者問答、原文含「畝」等中國大陸單位，資料品質偏弱，需另尋台灣官方栽培曆補齊。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="尚無官方季節資料（僅查得使用者問答等級的施肥/病蟲害資訊）"),
    dict(crop_id="huaqielan", name="花椰菜", category="花菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="官方資料依季節建議不同熟期品種（夏季早生耐熱、冬季晚生耐寒），顯示可透過品種選擇克服氣候差異，尚未取得明確北中南分區資料。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="全年皆可栽培，依季節選擇對應熟期品種（夏季早生耐熱／春秋中生／冬季晚生耐寒）"),
    dict(crop_id="xiaohuanggua", name="小黃瓜", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="官方資料列出早春（12～2月）、秋季（8～10月）、冬季（10～12月）等多套栽培期，暗示可透過設施栽培延長全年供應，尚未取得明確北中南分區資料。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="露地主要播種期3～10月，另有早春、秋季、冬季等設施栽培窗口，合計可全年安排播種"),
    dict(crop_id="malingshu", name="馬鈴薯", category="根莖類",
         region_north="不適合（冬季多雨，易發生晚疫病）",
         region_central="適合，中南部地區冬裡作為成熟產區（台中市、雲林、嘉義）",
         region_south="部分不適合（高屏區冬季日溫仍高，影響生育與結薯）",
         region_note="⚠️ 兩份官方/問答來源對播種月份有出入：主題館頁面指「中南部冬裡作」（通常指秋冬定植），但另一篇問答指「3月種植最好」，兩者矛盾，需另行查證台灣馬鈴薯官方栽培曆確認正確月份，故月份欄位暫不填入。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="中南部冬裡作為主，但確切播種月份的兩份來源互相矛盾，需查證後才能標示月份"),
    dict(crop_id="huluobo", name="胡蘿蔔", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文僅以「秋季／春天」等籠統季節詞描述；月份為將「秋季」「春天」推算為3～4月、9～10月的估算值，非原文直接給出的精確月份，需另行查證核實。",
         season_months_north=M(3,4,9,10), season_months_central=M(3,4,9,10), season_months_south=M(3,4,9,10),
         season_label="秋季耕種冬季收穫為主（推估9～10月），或反季節於春天栽種夏天收穫（推估3～4月）；原文未給精確月份，此為合理區間推算"),
    dict(crop_id="qiezi", name="茄子", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文僅提供生長溫度門檻，未明確標示適合播種季節，需另行查證。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示適合季節，僅知生長適溫白天20～25℃、夜間17℃以上，10℃以下停止生長"),
    dict(crop_id="tianjiao", name="甜椒", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="全國全年皆有產出（新竹、台中、彰化、南投、雲林、嘉義、高雄、屏東、台東等地），推測依產地輪替供應；尚未取得明確分區播種月份。",
         season_months_north=M(9,10,11), season_months_central=M(9,10,11), season_months_south=M(9,10,11),
         season_label="秋作最適合；春夏之際多雨高濕、高溫栽培困難（除非高冷地），冬作氣溫低且不穩定"),
    dict(crop_id="yangcong", name="洋蔥", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文僅以「台灣地區」統稱描述適合栽植時期，需另行查證分區差異。",
         season_months_north=M(9,10,11,12,1,2,3), season_months_central=M(9,10,11,12,1,2,3), season_months_south=M(9,10,11,12,1,2,3),
         season_label="秋冬季到隔年春季，須選短日型品種因應台灣日照較短"),
    dict(crop_id="sigua", name="絲瓜", category="果菜類",
         region_north="最適種植季節為春夏季（秋冬季溫度低而多雨）",
         region_central="主要種植於12月至隔年9月，立春前種植為佳，6月間生產最多",
         region_south="周年均可栽培，以秋冬季為主，冬季及早春由高屏地區供應全國所需",
         region_note="官方資料明確依北中南部給出不同種植月份與供應角色分工，是目前資料庫中地區差異最完整的一筆。",
         season_months_north=M(3,4,5,6,7,8), season_months_central=M(12,1,2,3,4,5,6,7,8,9), season_months_south=ALL_YEAR,
         season_label="北部春夏作；中部12月至隔年9月（立春前種植為佳）；南部全年可栽培，尤以秋冬季為主"),
    dict(crop_id="sijidou", name="四季豆", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料與適合季節，原文僅提供播種、株距、採收等栽培細節。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示適合季節，需另行查證；已知落花後10～15天為採收適期"),
    dict(crop_id="bale", name="芭樂", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="官方芭樂主題館定植頁面僅提及「容易積水的果園宜避免雨季定植」，未給出明確月份；月份是將台灣典型雨季/颱風季（約5～9月）排除後推算的「非雨季」窗口，非原文直接給出的月份，需另行查證核實。",
         season_months_north=M(10,11,12,1,2,3,4), season_months_central=M(10,11,12,1,2,3,4), season_months_south=M(10,11,12,1,2,3,4),
         season_label="容易積水的果園宜避免雨季定植（推估避開5～9月雨季/颱風季，其餘10月至翌年4月較適合）；此為推算區間，非原文直接給出的月份"),
    dict(crop_id="bocai", name="菠菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文為通俗種植教學（使用者問答等級），僅泛稱「全年均可種植，最好在秋冬季」。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="全年均可種植，最好在秋天和冬天種植"),
    dict(crop_id="tongao", name="茼蒿", category="葉菜類",
         region_north=M(9,10,11,12,1,2), region_central=M(9,10,11,12,1,2), region_south=M(9,10,11,12,1,2),
         region_note="原文明確指出3～8月因氣溫過高不適宜栽培，但未區分北中南部差異，暫以同一窗口套用三地區。",
         season_months_north=M(9,10,11,12,1,2), season_months_central=M(9,10,11,12,1,2), season_months_south=M(9,10,11,12,1,2),
         season_label="9月至翌年2月栽培，3～8月因氣溫過高不適宜"),
    dict(crop_id="jielan", name="芥藍", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文為通俗種植教學（使用者問答等級，內容偏向一般性園藝建議而非台灣在地技術資料）。",
         season_months_north=M(3,4,9,10,11), season_months_central=M(3,4,9,10,11), season_months_south=M(3,4,9,10,11),
         season_label="春季或秋季為最佳播種時間（原文為通俗教學文章，未細分月份與地區，需與台灣官方資料交叉核對）"),
    dict(crop_id="donggua", name="冬瓜", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料與適合季節，原文僅提供摘心整枝與施肥細節。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示適合季節，需另行查證"),
    dict(crop_id="nangua", name="南瓜", category="果菜類",
         region_north="3月播種最適宜",
         region_central="9、10月至翌年2月",
         region_south="9、10月至翌年2月",
         region_note="官方南瓜主題館明確區分北部與中南部的播種月份，中南部合併敘述（未進一步拆分中部/南部差異）。",
         season_months_north=M(3), season_months_central=M(9,10,11,12,1,2), season_months_south=M(9,10,11,12,1,2),
         season_label="中南部9、10月至翌年2月；北部3月播種最適宜"),
    dict(crop_id="kugua", name="苦瓜", category="果菜類",
         region_north="3～6月",
         region_central="2～9月",
         region_south="全年可栽培，冬季需選耐寒品種",
         region_note="官方苦瓜有機栽培管理頁面明確列出北中南三區各自的適合月份，資料完整度與絲瓜相當。",
         season_months_north=M(3,4,5,6), season_months_central=M(2,3,4,5,6,7,8,9), season_months_south=ALL_YEAR,
         season_label="北部3～6月，中部2～9月，南部全年可栽培（冬季需選耐寒品種）"),
    dict(crop_id="azhai", name="A菜（萵苣）", category="葉菜類",
         region_north="嫩莖萵苣8～2月；葉萵苣週年皆可栽植",
         region_central="嫩莖萵苣9～2月；葉萵苣週年皆可栽植",
         region_south="嫩莖萵苣9～2月中旬；葉萵苣週年皆可栽植",
         region_note="官方萵苣主題館依「嫩莖萵苣／不結球萵苣／結球萵苣／葉萵苣」四種類型分別列出北中南及高冷地適合季節，A菜屬葉萵苣類型，採該類數據。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="葉萵苣週年皆可栽植，以四月上旬至八月下旬較適；嫩莖萵苣則依地區分為8～2月（北部）、9～2月（中南部）"),
    dict(crop_id="yutou", name="芋頭", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文以「種植時間春節前後約2月」泛稱，內容偏通俗教學（qa等級），需另尋官方甘藷/芋頭主題館資料交叉核對。",
         season_months_north=M(2), season_months_central=M(2), season_months_south=M(2),
         season_label="種植時間約在春節前後（約2月），原文未細分地區，資料品質偏通俗教學需另行查證"),
    dict(crop_id="jiang", name="薑", category="根莖類",
         region_north="2～4月",
         region_central="12～4月",
         region_south="12～4月",
         region_note="原文明確區分北部與中南部種植月份，山地另有3～4月雨期種植的補充選項；資料來源標示不夠清楚是否為官方頁面，建議日後交叉核對改良場資料。",
         season_months_north=M(2,3,4), season_months_central=M(12,1,2,3,4), season_months_south=M(12,1,2,3,4),
         season_label="北部2～4月，中南部12～4月，山地可利用3～4月雨期種植"),
    dict(crop_id="wandou", name="豌豆", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="原文區分「平地」與「高冷地夏季」兩種栽培期，未明確標示對應北中南哪個地區，暫套用平地期作為通用值。",
         season_months_north=M(8,9,10,11,12,1), season_months_central=M(8,9,10,11,12,1), season_months_south=M(8,9,10,11,12,1),
         season_label="平地播種期8月下旬至翌年1月下旬；高冷地夏季栽培可於2～8月播種"),
    dict(crop_id="maodou", name="毛豆", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="主要產地為屏東、雲林、彰化（中南部），原文僅提供全國產期而非播種期，需另行查證播種月份與分區差異。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="全國產期集中在2、3、4、9、10、11月（此為採收上市月份，非播種月份，需另行查證播種期）"),
    dict(crop_id="ganju", name="柑橘（椪柑／柳橙／桶柑等）", category="果樹",
         region_north="桶柑、海梨柑、金柑為北部特產（宜蘭、新竹、苗栗等）",
         region_central="椪柑、柳橙主要產區（苗栗、台中、雲林、嘉義、南投、台南）",
         region_south="檸檬多產於屏東；白柚產於台南、嘉義",
         region_note="柑橘為多年生果樹，此處「地區」指的是各品種的傳統主產地分布，而非播種季節；不同品種產期橫跨全年（檸檬全年、文旦8月下旬、椪柑10月、柳橙11月、桶柑2月、晚崙西亞3-4月）。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="依品種而異，全年皆有品種採收：檸檬/萊姆全年、文旦8月下旬起、椪柑10月起、柳橙11月起、桶柑/茂谷柑2月起、晚崙西亞3-4月（此為採收期非播種期，果樹無「現在適合種」的月份概念）"),
    dict(crop_id="mangguo", name="芒果", category="果樹",
         region_north=None,
         region_central="高雄、台南（含）以北：7～8月抽梢，10～11月停梢，開花著果期2～3月",
         region_south="屏東：6～7月抽梢，9～10月停梢，開花著果期12～2月",
         region_note="定植頁面另有明確的苗木定植適期資料：3～10月均可定植，但應避開連續雨季、颱風天，及冬季寒流期間（低溫時苗木停梢不易發新根）；抽梢/開花物候期則是既有樹木的既有資料，兩者不同，此欄位使用的是苗木定植適期。",
         season_months_north=M(3,4,5,6,7,8,9,10), season_months_central=M(3,4,5,6,7,8,9,10), season_months_south=M(3,4,5,6,7,8,9,10),
         season_label="苗木定植適期3～10月均可，但應避開連續雨季、颱風天，及冬季（尤其寒流期間）；產期依品種與地區差異大，土芒果最早（6月前），凱特/紅凱特最晚（8～9月）"),
    dict(crop_id="mugua", name="木瓜", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，但已查得明確的全國定植適期：春植(2～3月)或秋植(9～11月)最適合，秋植在校園等環境更易成功；木瓜全年皆可定植，此為最適合的窗口。",
         season_months_north=M(2,3,9,10,11), season_months_central=M(2,3,9,10,11), season_months_south=M(2,3,9,10,11),
         season_label="定植時間以春植(2～3月)或秋植(9～11月)最適合，秋植較易成功；木瓜全年皆可定植但此為最佳窗口"),
    dict(crop_id="fengli", name="鳳梨", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="鳳梨種植時間需依目標採收月份反推計算（例如欲翌年4月採收則於前一年10月種植），並依繁殖芽種類調整種植季節，非單一固定月份，暫不列入「現在適合種」篩選。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="種植時間依目標採收月份反推計算，非固定月份；早春定植僅能用冠芽及吸芽繁殖"),
    dict(crop_id="lianwu", name="蓮霧", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文為苗木定植（多年生果樹建立期）的適合月份，非一般蔬菜播種概念。",
         season_months_north=M(2,3,10,11), season_months_central=M(2,3,10,11), season_months_south=M(2,3,10,11),
         season_label="苗木定植以2～3月或10～11月為宜（果樹為多年生作物，此為建立新植株的時機，非年年播種）"),
    dict(crop_id="yumi", name="玉米", category="雜糧",
         region_north=None, region_central=None,
         region_south="1月下旬～3月中旬、9月上中旬（兩次產期）",
         region_note="原文僅提供南部種植時間，超甜玉米適播期為9月上旬至10月上旬（未區分地區）；北部、中部播種期尚未取得資料。",
         season_months_north=None, season_months_central=None, season_months_south=M(1,2,3,9),
         season_label="南部1月下旬～3月中旬、9月上中旬可種植兩次；超甜玉米適播期9月上旬至10月上旬（地區未明）"),
    dict(crop_id="digua", name="地瓜（甘藷塊根）", category="雜糧",
         region_north="3～4月或6～8月插植",
         region_central="3～4月或6～8月插植",
         region_south="8～9月插植",
         region_note="官方甘藷主題館明確列出南部與中北東部不同插植適期，並依季別（春作/夏作/秋作）分別列出種植與收穫月份。",
         season_months_north=M(3,4,6,7,8), season_months_central=M(3,4,6,7,8), season_months_south=M(8,9),
         season_label="南部插植適期8～9月；中、北、東部插植適期3～4月或6～8月（春作1～4月種植6～10月收穫；夏作5～7月種植11～12月收穫；秋作8～11月種植翌年1～5月收穫）"),
    dict(crop_id="xiangjiao", name="香蕉", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料與適合季節，原文僅提供種植方式與株距密度規劃，屬多年生果樹，無年度播種月份概念。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示適合種植季節，需另行查證（香蕉為多年生果樹，以吸芽/種苗定植方式建立新植株）"),
    dict(crop_id="lvhuaqielan", name="青花菜（綠花椰）", category="花菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="⚠️ 本次查詢到的頁面內容經核對後實際描述的是花椰菜（白花椰）而非青花菜專屬資料，兩者同科同屬、栽培條件相近，但為避免張冠李戴，未直接引用該頁數據作為青花菜的正式資料，需另行查證青花菜專屬來源。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="尚無經核實的青花菜專屬季節資料，需另行查證（可先參考花椰菜的品種分期播種邏輯作為推測基礎，但不應直接視為青花菜數據）"),
    dict(crop_id="jiucai", name="韭菜", category="蔥蒜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文以「花蓮地區」為例說明施肥技術，全台適用性需另行查證；官方明確指出夏季不易生長，秋冬春品質較佳。",
         season_months_north=M(11,12,1,2,3), season_months_central=M(11,12,1,2,3), season_months_south=M(11,12,1,2,3),
         season_label="播種適期11月至翌年3月；分株法適期11～12月；雖全年可栽培，但夏季高溫長日照易使纖維變粗、抽苔，品質下降"),
    dict(crop_id="cong", name="蔥", category="蔥蒜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文區分「一般種植」與「北蔥」兩種類型，後者全年皆可種植但以夏後為佳。",
         season_months_north=M(8,9,10), season_months_central=M(8,9,10), season_months_south=M(8,9,10),
         season_label="種植時期以8～10月播種為佳；北蔥全年均可種植，但以夏後為佳"),
    dict(crop_id="dasuan", name="大蒜", category="蔥蒜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文為官方大蒜主題館資料，播種期敘述明確但未進一步分區。",
         season_months_north=M(9,10,11,12), season_months_central=M(9,10,11,12), season_months_south=M(9,10,11,12),
         season_label="國曆9～12月均可播種，蒜頭栽培宜9月中旬至10月中旬播種"),
    dict(crop_id="xigua", name="西瓜", category="果菜類",
         region_north=None, region_central=None, region_south="冬季亦可栽培（深冬寒流時需用稻草防寒度過幼苗期），初春採收",
         region_note="官方農產品產期產地資料顯示全國產期為3～11月，主要產地集中南部（台南、高雄、屏東）與東部（花蓮、宜蘭），north/central分區資料尚未取得。",
         season_months_north=M(3,4,5,6,7,8,9,10,11), season_months_central=M(3,4,5,6,7,8,9,10,11), season_months_south=ALL_YEAR,
         season_label="全國產期3～11月，盛產期4～8月；南部冬季氣溫仍適合栽種，深冬寒流時用稻草防寒即可安全越冬，初春採收"),
    dict(crop_id="jiecai", name="芥菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="主要栽培地區分布於桃園、苗栗、新竹、彰化、嘉義、雲林等縣，尚未取得北中南分區的季節差異資料。",
         season_months_north=M(9,10,11,12,1,2), season_months_central=M(9,10,11,12,1,2), season_months_south=M(9,10,11,12,1,2),
         season_label="主要栽培期為秋冬季，適合溫度16～22℃、日夜溫差大時品質最佳（原文未給出精確播種月份，此為「秋冬季」的合理月份區間）"),
    dict(crop_id="youcai", name="油菜", category="雜糧",
         region_north=None, region_central=None, region_south=None,
         region_note="原文以「台東地區」為例說明產期，全台適用性需另行查證；常作為綠肥及花海景觀作物栽培，而非食用蔬菜為主要目的。",
         season_months_north=M(11,12,1), season_months_central=M(11,12,1), season_months_south=M(11,12,1),
         season_label="台東地區種植期為二期稻作收穫後(11月下旬)至立春(2月上旬)，開花期約45天；發芽適溫20～25℃，生育適溫15～20℃"),
    dict(crop_id="lizhi", name="荔枝", category="果樹",
         region_north="新竹地區成熟較晚（7月中上旬）",
         region_central="南投、台中地區6月中下旬成熟",
         region_south="高屏地區最早成熟（5月初）；嘉南地區6月初成熟",
         region_note="官方荔枝主題館明確依地區列出黑葉品種的成熟期差異，由南向北依序推進；此處的季節欄位是「苗木定植適期」，與採收期是不同概念。",
         season_months_north=M(2,3,4,10,11), season_months_central=M(2,3,4,10,11), season_months_south=M(2,3,4,10,11),
         season_label="苗木定植適期為2～4月及10～11月（果樹為多年生作物，此為建立新植株的時機）；全台產期依地區與品種從5月初(南部)持續至8月初(中海拔山區)"),
    dict(crop_id="longyan", name="龍眼", category="果樹",
         region_north=None, region_central=None, region_south="南部地區果實較早成熟",
         region_note="官方龍眼主題館提供嫁接、高壓、種子三種繁殖法的適期，嫁接為最常用的苗木繁殖方式；花芽分化期需感受12～1月的15～22℃涼溫持續8～10週。",
         season_months_north=M(1,2,3), season_months_central=M(1,2,3), season_months_south=M(1,2,3),
         season_label="苗木嫁接繁殖主要適期1～3月（高壓法全年皆可進行）；果實產期7～9月，南部較早成熟"),
    dict(crop_id="baixiangguo", name="百香果", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文以「埔里大坪頂地區」（設施＋冬季電照技術）與「平地」兩種栽培模式對比產期，未細分行政區。",
         season_months_north=M(8,9,2,3), season_months_central=M(8,9,2,3), season_months_south=M(8,9,2,3),
         season_label="播種適期以8、9月或2、3月最合適（一年四季皆可播種）；扦插法全年可行，以3～4月與9～10月最合適；平地穩定產季集中在當年12月至隔年7月"),
    dict(crop_id="huolongguo", name="火龍果", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；扦插種植季節「春天3～5月」一說來自多篇搜尋結果綜合整理，未找到單一可核實的官方頁面明確佐證，故season欄位暫不填入精確月份，需另行以WebFetch查證官方原文。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="適合溫度17～25℃（20℃左右花芽正常萌發）；扦插種植季節一般認為以春天3～5月氣候溫和生根較快，但此說法尚未經WebFetch查證單一官方來源，需另行確認"),
    dict(crop_id="shanyao", name="山藥", category="根莖類",
         region_north="北部地區主要害蟲包含神澤氏葉蟎、優美藺葉蜂、薊馬、介殼蟲、椿象、毒蛾、斜紋夜盜、金龜子等",
         region_central=None, region_south=None,
         region_note="尚未取得完整北中南分區種植資料，僅查得北部地區的病蟲害清單。",
         season_months_north=M(2,3,4), season_months_central=M(2,3,4), season_months_south=M(2,3,4),
         season_label="無性繁殖（種薯）於清明節前後或2～4月間進行；塊莖生長發育於11～12月達最高峰"),
    dict(crop_id="niupang", name="牛蒡", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，此筆為通俗種植教學等級（qa），需另尋台灣官方牛蒡栽培資料交叉核對。",
         season_months_north=M(2,3,7,8), season_months_central=M(2,3,7,8), season_months_south=M(2,3,7,8),
         season_label="春初2～3月播種，或初秋7～8月播種；直播或移栽後第二年秋季採收"),
    dict(crop_id="lusun", name="蘆筍", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="官方蘆筍主題館區分「穴盤苗」與「田間苗」兩種定植方式的適合季節，尚未取得北中南分區差異。",
         season_months_north=M(3,4,9,10,11), season_months_central=M(3,4,9,10,11), season_months_south=M(3,4,9,10,11),
         season_label="田間苗定植：春季3月下旬至4月上旬（最適宜）、秋季10月上旬至11月中旬；應避免6～8月高溫多雨定植。穴盤苗任何季節皆可定植，但須避開颱風期"),
    dict(crop_id="jiaobaisun", name="茭白筍", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料與明確的分株定植月份，原文提供的是採收期（依品種而異）而非種植月份。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="以留母莖分株法無性繁殖，原文未明確標示分株定植月份；青殼種產期4～11月，赤殼種產期9～11月中旬，搭配夜間電照技術可全年生產"),
    dict(crop_id="hongdou", name="紅豆", category="豆菜類",
         region_north=None, region_central=None,
         region_south="高屏地區為主要秋作栽培區",
         region_note="紅豆為短日照植物，台灣春夏作因長日照與高溫延遲開花、結莢不良，故官方明確指出「適於南部秋作栽培」；北部、中部分區資料尚未取得。",
         season_months_north=None, season_months_central=None, season_months_south=M(9,10),
         season_label="播種適期9月中旬至10月上旬（南部秋作為主），播種至成熟平均90天，生育期約80～95天"),
    dict(crop_id="huasheng", name="花生", category="雜糧",
         region_north=None, region_central=None, region_south=None,
         region_note="主要栽培地區分布於雲林、彰化、嘉義（中部平原為主），尚未取得明確北中南分區季節差異；season欄位是依「農曆採收期＋成長期4個月」反推的播種月份估算，非原文直接給出的播種月份。",
         season_months_north=M(2,3,4,7,8,9), season_months_central=M(2,3,4,7,8,9), season_months_south=M(2,3,4,7,8,9),
         season_label="春作（春豆）約國曆2～4月播種、農曆5～7月採收；秋作（冬豆）約國曆7～9月播種、農曆10～12月採收；此月份為根據成長期4個月反推估算，非原文直接給出的播種月份"),
    dict(crop_id="putao", name="葡萄", category="果樹",
         region_north=None,
         region_central="主要產地彰化溪湖/大村、台中新社、南投信義、苗栗卓蘭",
         region_south=None,
         region_note="葡萄為多年生果樹，此處資料是既有植株的產期調節模式（修剪期／採收期），並非新植苗木的種植月份；一年二收模式與一年一收模式（南投水里、信義）的修剪與採收時程不同。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="多年生果樹，無播種月份概念；一年二收模式第一收2～3月修剪、7～8月採收，第二收約12～1月採收（依地區與模式略有差異）"),
    dict(crop_id="caomei", name="草莓", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，草莓在台灣多集中於中部山區（如大湖、內湖）栽培，但本次未查得明確產地分布原文。",
         season_months_north=M(9,10), season_months_central=M(9,10), season_months_south=M(9,10),
         season_label="定植期為9月底至10月中旬（走莖小苗健康選種後定植）；產期12月至隔年4月中旬，農曆年後為盛產期；適溫15～25℃"),
    dict(crop_id="qiukui", name="秋葵", category="果菜類",
         region_north="4～8月栽培",
         region_central="4～8月栽培",
         region_south="3～9月栽培",
         region_note="南部生長季較長（3～9月），中北部略短（4～8月）；此區域劃分來自搜尋摘要整理而非單一WebFetch核實頁面，播種窗口（春作3～4月、秋作8～9月）則已核實原文。",
         season_months_north=M(4,8), season_months_central=M(4,8), season_months_south=M(3,4,8,9),
         season_label="春作3～4月間播種，秋作8～9月間播種（播種不可太遲，遇寒流會嚴重影響產量）；南部生長適期3～9月，中北部4～8月"),
    dict(crop_id="huanggongcai", name="皇宮菜（落葵）", category="葉菜類",
         region_north=None, region_central=None, region_south="台東地區可於3月之後以種子直播或扦插方式栽培",
         region_note="尚未取得完整北中南分區資料，僅查得台東（東部）案例；本筆資料整體為通俗種植教學等級（qa）。",
         season_months_north=M(3,4,5,6,7,8,9,10), season_months_central=M(3,4,5,6,7,8,9,10), season_months_south=M(3,4,5,6,7,8,9,10),
         season_label="耐熱不耐寒，扦插繁殖約1週長根；盛產期4～10月；台東地區3月之後可種子直播或扦插"),
    dict(crop_id="jiucengta", name="九層塔", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，本筆為通俗種植教學等級（qa），需另尋官方九層塔/羅勒栽培資料交叉核對。",
         season_months_north=M(5,6,7,8,9,10), season_months_central=M(5,6,7,8,9,10), season_months_south=M(5,6,7,8,9,10),
         season_label="全年均可栽種，以5～10月最佳；高溫是發芽及生長的必要條件，5月中旬後播種最理想；平均採收約需40天"),
    dict(crop_id="xiangcai", name="香菜（芫荽）", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，本筆為通俗種植教學等級（qa），需另尋官方芫荽栽培資料交叉核對。",
         season_months_north=M(9,10,11,12,1,2,3), season_months_central=M(9,10,11,12,1,2,3), season_months_south=M(9,10,11,12,1,2,3),
         season_label="喜冷涼不耐熱，生長適溫15～18℃、30℃以上停止生長，台灣以春、秋、冬季較適合種植；夏季栽培需低溫催芽處理"),
    dict(crop_id="lianou", name="蓮藕", category="根莖類",
         region_north="約晚南部2～3星期，因生育初期氣溫較低，採收也約晚1個月",
         region_central="3月中旬至4月下旬定植",
         region_south="2月中旬至4月中旬定植，6～8月即可陸續採收",
         region_note="官方資料明確給出南部與中北部不同定植適期，並說明北部因氣溫較低導致生育與採收皆較晚，是本資料庫中根莖類地區資料最完整的案例之一。",
         season_months_north=M(3,4), season_months_central=M(3,4), season_months_south=M(2,3,4),
         season_label="南部定植適期2月中旬至4月中旬；中北部3月中旬至4月下旬（北部較南部晚2～3星期）；過早栽植會因氣溫過低使發芽緩慢、生長不佳"),
    dict(crop_id="yangtao", name="楊桃", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="生長環境「以北迴歸線以南、不易有寒害地區栽植較適宜」，暗示南部較適合，但原文未給出明確定植月份，故season欄位暫不填入；果樹為多年生作物，嫁接苗約9個月後可著果，定植苗需2～3年才開花結果。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示定植適期月份，需另行查證；全年可生產，但產量集中在10月至翌年3月"),
    dict(crop_id="shijia", name="釋迦", category="果樹",
         region_north=None, region_central=None,
         region_south="台東為主要產地",
         region_note="秋冬季易結霜地區不適宜栽植，暗示南部（尤其台東）較適合；官方資料明確給出定植適期月份，是本次少數有精確「苗木定植月份」的果樹之一。",
         season_months_north=M(1,2), season_months_central=M(1,2), season_months_south=M(1,2),
         season_label="定植適期為翌年1～2月，於苗木落葉後新芽萌發前定植；生育溫度15～32℃間最佳；產期經產期調節後全年皆有，8～9月及12～1月為盛產期，4～6月為無果期"),
    dict(crop_id="tianshi", name="甜柿", category="果樹",
         region_north="台中以北海拔600～1,000公尺",
         region_central="南投及嘉義海拔900～1,300公尺",
         region_south=None,
         region_note="甜柿適栽區以「海拔」而非行政區南北劃分，台中以北需海拔600～1,000公尺、南投嘉義需900～1,300公尺才符合溫度條件，屬於高冷地栽培邏輯（與高麗菜、花椰菜類似），非平地可種植的作物。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="多年生果樹，栽植4～5年後才開始結果；原文未明確標示定植月份，需另行查證；產期約9～11月，富有甜柿品種10月下旬至11月下旬"),
    dict(crop_id="yangxiangua", name="洋香瓜（哈密瓜／香瓜）", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="宜蘭地區的哈密瓜主要產期為端午節前後（來自搜尋摘要，未經WebFetch單獨核實），全國官方產期資料則涵蓋5～12月；北中南分區種植資料尚未取得。",
         season_months_north=M(5,6,7,8,9,10,11,12), season_months_central=M(5,6,7,8,9,10,11,12), season_months_south=M(5,6,7,8,9,10,11,12),
         season_label="全國官方產期5月至12月；網紋洋香瓜以12月至翌年3月生產最穩定，光皮洋香瓜以11月中旬至翌年3月底品質較穩定（此細節來自搜尋摘要整理，未逐一以WebFetch核實）"),
    dict(crop_id="longxucai", name="龍鬚菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="龍鬚菜為佛手瓜(隼人瓜)植株的嫩梢部分，非獨立作物；尚未取得北中南分區資料。",
         season_months_north=M(4,5,6,7,8,9,10), season_months_central=M(4,5,6,7,8,9,10), season_months_south=M(4,5,6,7,8,9,10),
         season_label="全國官方產期4～10月；生育適溫18～28℃，12℃以下停止生長，超過30℃生長勢較弱；夏季每3天、冬季每10天採收一次"),
    dict(crop_id="shansu", name="山蘇", category="葉菜類",
         region_north=None, region_central=None,
         region_south="人工栽培以花蓮縣及屏東縣最多",
         region_note="廣泛分布於台灣中低海拔(500～2,500公尺)山區，人工栽培集中花蓮、屏東（東部與南部），北部、中部人工栽培資料尚未取得。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="一年四季皆可採食，夏季高溫期生長快速、冬季低溫期生長緩慢；耐旱但忌強光，需遮蔭潮濕環境"),
    dict(crop_id="guomao", name="過貓（過溝菜蕨）", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，為原住民族農產業主題館收錄的原生蕨類野菜。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="一年四季均可種植，以春季最適宜；產期集中夏季，雨水越多生長越佳，5～10月為盛產期，8～9月產量最多，適合颱風季節作為葉菜替代來源"),
    dict(crop_id="tiancaigen", name="甜菜根", category="根莖類",
         region_north="平地10～11月播種",
         region_central="平地10～11月，高冷地3～4月播種",
         region_south="平地10～11月播種",
         region_note="官方資料明確區分「平地」與「高冷地」播種適期，台灣高冷地主要分布於中部山區，故中部欄位同時保留兩種選項；秋冬雲嘉地區為主要產區。",
         season_months_north=M(10,11), season_months_central=M(3,4,10,11), season_months_south=M(10,11),
         season_label="平地播種適期10～11月，高冷地播種適期3～4月；生育適溫15～20℃，生長期60～80天，台灣盛產於冬季"),
    dict(crop_id="biqi", name="荸薺（馬蹄）", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文僅以「春末」描述栽植時間，未給出精確月份。",
         season_months_north=M(4,5), season_months_central=M(4,5), season_months_south=M(4,5),
         season_label="春末將種球淺植於土中（此處以「春末」推估為4～5月），栽培到收穫約120天；生育適溫30～35℃，球莖肥大期宜降至22～26℃；產期11月至翌年3月，早熟種11～12月、晚熟種12月至翌年3月"),
    dict(crop_id="pingguo", name="蘋果", category="果樹",
         region_north="桃園復興鄉有零星栽培",
         region_central="台中和平區為主要產區（梨山、福壽山、武陵農場等高冷地）",
         region_south=None,
         region_note="蘋果需年平均溫9～14℃、冬季7.2℃以下低溫累積達1,400小時以上，台灣僅高冷地（梨山等）可栽培；平地雖可種植熱帶蘋果品種，但官方明確指出「尚不建議經濟栽培」，果實會偏小。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="高冷地栽培為主，原文未明確標示苗木定植月份；花期約農曆12月至翌年1月，結果期4、5月；平地熱帶蘋果需人工於農曆11月底強迫落葉以促進開花"),
    dict(crop_id="pipa", name="枇杷", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；生育週期特殊（一年培苗、二年移栽、三年嫁接、四年定植、十年進入旺盛期），原文未明確標示各階段對應的月份。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示定植月份，需另行查證；產期12月至翌年5月，盛產期3～4月；第1次施肥8～9月開花前，第2次11～12月花瓣脫落後至翌年1月，第3次約4月"),
    dict(crop_id="hongzao", name="紅棗", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；果樹幼年期較其他果樹短，前3年整枝配置枝條位置，第4年開始結果採收。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示定植月份，需另行查證；3月萌芽開花，7～8月為採收期，果實生長期約1個月"),
    dict(crop_id="laoli", name="酪梨", category="果樹",
         region_north=None,
         region_central="嘉義地區為主要栽培區（嘉選一號、三號、四號）",
         region_south="麻豆地區（嘉選二號）",
         region_note="官方酪梨主題館明確給出定植適期月份，且各品種依栽培地區產期不同（嘉選四號最早6月中～7月中採收，Choquette最晚可至12月上旬）。",
         season_months_north=M(3,4,11), season_months_central=M(3,4,11), season_months_south=M(3,4,11),
         season_label="定植適期為春季3～4月和秋季11月；產期依品種而異，早熟種6～8月、中熟種8～10月、晚熟種10月至翌年2月採收"),
    dict(crop_id="dadou", name="大豆（黃豆）", category="雜糧",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料，原文僅泛稱播種時程，未區分地區。",
         season_months_north=M(5,6), season_months_central=M(5,6), season_months_south=M(5,6),
         season_label="5月播種（不遲於6月），10月收成；生長季約4個月，發芽適溫10～12℃，生育適溫15～25℃"),
    dict(crop_id="jinzhen", name="金針", category="特用作物",
         region_north="本地種(高山種)需北部海拔400公尺以上山區才能穩定抽苔開花",
         region_central=None,
         region_south=None,
         region_note="本地種(高山種)對海拔要求高，平地種「台東6號」則全台皆能栽培開花，冬季葉片會乾枯休眠；主要產區在花蓮、台東的高山地帶。",
         season_months_north=M(3,4,5,9,10,11), season_months_central=M(3,4,5,9,10,11), season_months_south=M(3,4,5,9,10,11),
         season_label="分株繁殖除冬季低溫期外全年皆可進行；種子繁殖以春秋兩季播種成活率較高；本地種產季為秋季7月下旬至9月中旬，台東6號產季為夏季5月上旬至6月中旬"),
    dict(crop_id="xiancao", name="仙草", category="特用作物",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；主要以扦插繁殖，8月於本田選健壯莖插植於苗圃育苗，翌年2～3月挖取種苗移植本田。",
         season_months_north=M(2,3), season_months_central=M(2,3), season_months_south=M(2,3),
         season_label="扦插育苗於8月間進行，翌年2～3月重新萌發新枝時移植本田（此欄位採用移植本田的月份）；生育適溫20～25℃；花期10～12月，以頂芽腋芽長出花蕾時採收"),
    dict(crop_id="luoshenkui", name="洛神葵", category="特用作物",
         region_north=None, region_central="南投縣有零星種植",
         region_south="台東縣栽培最多（鹿野、卑南、金峰、太麻里等鄉鎮）；花蓮縣、雲林縣亦有種植",
         region_note="官方資料明確給出播種月份，主要產區集中台灣東部（台東最多）與零星中南部地區。",
         season_months_north=M(4,5,6), season_months_central=M(4,5,6), season_months_south=M(4,5,6),
         season_label="播種期4～6月，生長期約4個月；早生種產期8～9月，中生種10～11月，晚生種12月至翌年1月，盛產期8～10月"),
    dict(crop_id="kafei", name="咖啡", category="特用作物",
         region_north=None, region_central="雲林古坑為最著名產區",
         region_south=None,
         region_note="官方咖啡主題館明確給出定植適期，古坑咖啡9月以後進入採收期；主要產區為雲林古坑（中部丘陵地），亦有零星種植於南投、屏東等地。",
         season_months_north=M(12,1,2,3), season_months_central=M(12,1,2,3), season_months_south=M(12,1,2,3),
         season_label="種子可於秋季10～12月及春季2～4月間播種，植株定植時間以12～3月最適合；生育適溫16～28℃，年降雨量1500～2500毫米較適宜"),
    dict(crop_id="lingjiao", name="菱角", category="根莖類",
         region_north=None, region_central=None,
         region_south="台南官田為全國最大產區（面積與產量皆最高，占全國約90%產量）",
         region_note="尚未取得北中南分區的精確種植月份，搜尋摘要提及約2月初或4～5月移植等不同說法，未經WebFetch單一官方頁面核實，season欄位暫不填入以避免誤導。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="適合種植季節與確切月份尚待以官方原文核實（搜尋摘要提及約2月初育苗、部分地區4～5月移植，但未能找到單一可核實來源）；產期8月開始，9～11月盛產"),
    dict(crop_id="yelian", name="野蓮（龍骨瓣莕菜）", category="葉菜類",
         region_north=None, region_central=None,
         region_south="高雄美濃為最著名產區",
         region_note="野蓮為全年生水生植物，於魚塭或池塘中持續栽培採收，非傳統「播種季節」概念的作物；此資料整體為搜尋摘要整理（qa等級），需另尋官方原文核實。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="全年生水生植物，於魚塭/池塘持續栽培；夏季生長較快約2個月可採收，冬季較慢約3個月，一年可採收3～4次（換季種植間會曬池數天）"),
    dict(crop_id="shudou", name="樹豆", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="台灣各地零星栽培，大多於海拔1,000公尺以下淺山坡地、丘陵地及河床地，尚未取得北中南分區資料；原文未明確標示播種月份，僅知花果期春夏間。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示播種月份，需另行查證；為一年至多年生矮灌木，耐貧瘠乾旱但不耐寒忌霜害，花序無限型生長使開花結莢時間參差不一，花果期春、夏間"),
    dict(crop_id="taiwanli", name="台灣藜", category="特用作物",
         region_north=None, region_central=None,
         region_south="花蓮、台東、屏東原住民部落有少量栽培",
         region_note="台灣原生種植物，原住民部落已耕種百年以上，常作為小米、玉米的伴生作物；原文未明確標示播種月份。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示播種月份，需另行查證；播種後90～100天即可成熟（依季節及品系而異）；植株耐旱耐瘠性極佳"),
    dict(crop_id="xiaomi", name="小米", category="雜糧",
         region_north=None, region_central=None,
         region_south="主要種植於台東地區及高屏地區",
         region_note="官方小米及台灣藜主題館明確指出台灣以春、秋兩作皆可種植，春作產量較佳；月份是依台灣常見雜糧作物春秋作習慣推估（春作約2～4月、秋作約8～10月），非原文直接給出的精確月份。",
         season_months_north=M(2,3,4,8,9,10), season_months_central=M(2,3,4,8,9,10), season_months_south=M(2,3,4,8,9,10),
         season_label="春、秋兩作皆可種植，春作產量較秋作佳（秋作受天災影響機率較大）；生育期3.5～4個月，發芽適溫18～24℃，開花期5～10月"),
    dict(crop_id="ningmeng", name="檸檬", category="果樹",
         region_north=None, region_central=None,
         region_south="屏東為主要產區",
         region_note="尚未取得定植適期的官方原文佐證（搜尋多篇資料未查得明確月份），season欄位暫不填入；台灣主要品種優利卡(Eureka)容易周年開花結果，故俗稱四季檸檬。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="定植適期原文未明確標示，需另行查證；經產期調節全年均可生產，開花期12～2月，盛產期6～8月及10～12月"),
    dict(crop_id="hongcongtou", name="紅蔥頭", category="蔥蒜類",
         region_north=None, region_central=None,
         region_south="台南為主要產區",
         region_note="尚未取得單一WebFetch核實來源，此資料整理自搜尋摘要（qa等級），需另行查證台灣官方紅蔥頭栽培曆核實。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="最佳種植季節為秋季，但台灣幾乎全年可種植；發芽適溫15～30℃（20℃最適）；種球需日照6週以上休眠期才能再種"),
    dict(crop_id="lajiao", name="辣椒", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將辣椒列入全國適用41項；本次查證的頁面未區分北中南部季節差異（僅泛稱全台適用），需另行查證是否有分區資料。",
         season_months_north=M(2,3,4,8,9,10), season_months_central=M(2,3,4,8,9,10), season_months_south=M(2,3,4,8,9,10),
         season_label="全年皆可栽種，考量本土季風氣候以春作及初秋較合適；種子發芽適溫25～30℃，生長溫度15～30℃；採收期約可達3個月"),
    dict(crop_id="qingjiangcai", name="青江菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將青江菜列為短期葉菜類全國適用項目之一；尚未取得北中南分區資料。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="除嚴冬外整年皆可栽培；春秋季播種45～50天、夏季35～40天可收成"),
    dict(crop_id="qincai", name="芹菜", category="葉菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；性喜冷涼，夏季需中高海拔或降溫設施才容易生長。",
         season_months_north=ALL_YEAR, season_months_central=ALL_YEAR, season_months_south=ALL_YEAR,
         season_label="全年生產之葉菜類，盛產期為春、秋、冬季，夏季需中高海拔或降溫設施"),
    dict(crop_id="bianbu", name="扁蒲（蒲瓜）", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將扁蒲列入全國適用41項；原文未明確標示播種季節月份，僅提供溫度偏好與整枝採收細節，season欄位暫不填入。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示播種季節，需另行查證；種子發芽適溫25～30℃，生長發育適溫25～28℃，結果適溫20～25℃，高溫期生育較旺盛"),
    dict(crop_id="hugua", name="胡瓜（花胡瓜）", category="果菜類",
         region_north=None, region_central=None,
         region_south="高屏地區周年可生產，往年以秋冬裡作為主要產期",
         region_note="農業部「地方特色作物」清單將胡瓜列入全國適用41項；官方資料明確指出高屏地區(南部)周年可生產，北部、中部分區資料尚未取得。",
         season_months_north=None, season_months_central=None, season_months_south=ALL_YEAR,
         season_label="高屏地區周年可生產，以秋冬裡作為主要產期，盛產季節集中冬、春兩季；播種後40～45天開花，開花後5～7天採收"),
    dict(crop_id="jianghuang", name="薑黃", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；農業部「地方特色作物」清單將薑黃列為新北市、南投等多縣市的區域特色作物。",
         season_months_north=M(3,4,5), season_months_central=M(3,4,5), season_months_south=M(3,4,5),
         season_label="種植適期3～5月，以4月份種植最佳；種植後約8～10個月可收穫，收穫期12月至翌年2月"),
    dict(crop_id="lanmei", name="藍莓", category="果樹",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料與明確定植月份；南方高叢藍莓與兔眼藍莓因低溫需求較低，較適合台灣氣候。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示定植月份，需另行查證；11月起零星開花，3～4月盛花，4～5月中果實開始成熟，產季5～10月（7月為高峰），開花至採收約60～90天"),
    dict(crop_id="huangdidou", name="皇帝豆（萊豆）", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="尚未取得北中南分區資料；原文提及若7～8月種植，幼苗根部可能因塑膠布日照高溫受損（需覆蓋稻草降溫），暗示此非最理想播種時機，但確切最適播種月份原文未直接給出，season欄位暫不填入。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未直接給出最適播種月份（僅知7～8月種植需額外防護日曬），需另行查證；採收期11月至翌年5月，長達6～7個月，冬春季為盛產期；生長適溫15～25℃，短日照植物"),
    dict(crop_id="qiujingganlan", name="球莖甘藍（結頭菜）", category="根莖類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將球莖甘藍列為彰化縣、雲林縣區域發展專項作物；尚未取得北中南分區資料。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示播種月份，需另行查證（喜冷涼氣候，耐寒耐霜，與同為十字花科的高麗菜特性相近）；播種育苗移植後，早生種55～60天可採收，晚生種80～100天可採收"),
    dict(crop_id="yuegua", name="越瓜（醃瓜）", category="果菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將越瓜列為台中市、彰化縣、雲林縣、嘉義市/縣等多縣市的區域特色作物；本筆季節資料來自搜尋摘要整理（qa等級），需另行查證官方原文核實確切月份。",
         season_months_north=M(3,4,5,6), season_months_central=M(3,4,5,6), season_months_south=M(3,4,5,6),
         season_label="性喜高溫多濕，台灣一般在春季至夏季栽種"),
    dict(crop_id="jiangdou", name="豇豆（長豆）", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將長(豇)豆列為全國適用41項；原文未明確標示播種月份，需另行查證。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示播種月份，需另行查證；性喜日照充足氣候，耐熱性強、耐寒性弱；台灣多栽培蔓性長豇豆，需立支架；開始採收後每1～2天可採收一次"),
    dict(crop_id="midou", name="米豆", category="豆菜類",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將米豆列為全國適用41項；原文未明確標示播種月份，多與玉米間作。",
         season_months_north=None, season_months_central=None, season_months_south=None,
         season_label="原文未明確標示播種月份，需另行查證；生長適溫25～35℃，大多具短日開花特性，在東南亞地區常與玉米間作"),
    dict(crop_id="ganzhe", name="甘蔗", category="雜糧",
         region_north=None, region_central=None, region_south=None,
         region_note="農業部「地方特色作物」清單將食用甘蔗列為全國適用41項；官方資料明確給出春植、秋植、補植三個種植期。",
         season_months_north=M(1,2,3,7,8), season_months_central=M(1,2,3,7,8), season_months_south=M(1,2,3,7,8),
         season_label="春植期1～3月，秋植期7～8月，補植期1～5月；生長期約18個月；收成尖峰期為12月至翌年4月"),
    dict(crop_id="huma", name="胡麻（芝麻）", category="雜糧",
         region_north=None, region_central="台南市西港、安定、善化、將軍、佳里等區為主要產地",
         region_south=None,
         region_note="官方胡麻主題館明確給出春秋兩作的採收期，播種月份是依生育期(80～90天)反推估算，非原文直接給出的精確月份，需另行查證核實。",
         season_months_north=M(3,4,8,9), season_months_central=M(3,4,8,9), season_months_south=M(3,4,8,9),
         season_label="春、秋兩作皆可栽培，台灣以秋作面積較大、產量較多；春作採收6～7月、秋作採收11月中至12月（此處播種月份為依生育期80～90天反推估算，非原文直接給出）"),
    dict(crop_id="hangju", name="杭菊", category="特用作物",
         region_north=None, region_central=None,
         region_south=None,
         region_note="農業部「地方特色作物」清單將杭菊列為苗栗縣區域特色作物；主要產地在苗栗銅鑼；種植月份來自搜尋摘要整理（qa等級），田間定植規格已以WebFetch核實官方原文。",
         season_months_north=M(4,5,6,7), season_months_central=M(4,5,6,7), season_months_south=M(4,5,6,7),
         season_label="一般於4月清明節後開始種植，最晚可於7月前；花期11～12月；生長適溫15～28℃，耐旱不耐淹水"),
]

CULTIVATION = [
    # 小白菜 - 農業知識入口網 knowledge_view id=787
    ("xiaobaicai", "適合季節", "四季皆可栽種，以春、秋兩季為佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "最適溫度", "20～25℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "土壤條件", "肥沃、疏鬆、保水、排水良好之砂質壤土", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "播種方式", "撒播法，種子均勻撒播於土上，覆薄土約0.5公分", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "株距", "約15～20公分（需經1～2次間拔）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "水分管理", "不耐旱，須保持土壤濕潤，早晚各澆一次水", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "施肥", "種植約10天後視基肥與生長狀況適度追肥，可株間施肥或噴灑有機液肥", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),
    ("xiaobaicai", "採收天數", "約25～30天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=787", "official", "2026-08-19"),

    # 地瓜葉 - 農業知識入口網 knowledge_view id=2355（使用者問答，資料品質較弱，缺季節/溫度/土壤/株距/施肥）
    ("digualve", "種植方式", "取帶梗地瓜葉，將梗部埋入土中、部分留在外面扦插，每截枝條需有氣根以提高存活率", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2355", "qa", "2026-08-19"),
    ("digualve", "發芽時間", "約3～5天開始發芽", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2355", "qa", "2026-08-19"),
    ("digualve", "採收天數", "約20～30天可採收", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2355", "qa", "2026-08-19"),
    ("digualve", "水分管理", "每天澆水，不用太多水，但需補給充足水分", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2355", "qa", "2026-08-19"),
    ("digualve", "光照", "需充足陽光", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2355", "qa", "2026-08-19"),
    ("digualve", "採收方式", "長大後需持續採收，越摘生長越快、越嫩，不採收則老化", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2355", "qa", "2026-08-19"),

    # 番茄（小果） - 農業知識入口網 subject id=32584（正式栽培技術頁）
    ("fanqie", "適合季節（北部）", "秋冬作低溫多濕不適宜，春、夏作均可種植", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=32584", "official", "2026-08-19"),
    ("fanqie", "適合季節（中南部）", "全年均可種植", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=32584", "official", "2026-08-19"),
    ("fanqie", "土壤條件", "土層深厚、富有機質、排水良好之砂質壤土，pH5.6～7.5", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=32584", "official", "2026-08-19"),
    ("fanqie", "株距（春秋作）", "行株距75～150×60公分，四幹整枝後放任", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=32584", "official", "2026-08-19"),
    ("fanqie", "株距（夏作）", "行株距75～150×45公分，六幹整枝後放任", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=32584", "official", "2026-08-19"),
    ("fanqie", "夏作高溫處理", "夜溫高於24℃、日溫高於32℃時，需用植物生長調節劑噴於2～3朵小花盛開之花序以促進著果", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=32584", "official", "2026-08-19"),

    # 空心菜 - 農業知識入口網 knowledge_view id=8282
    ("kongxincai", "植物特性", "耐熱、喜濕、生長迅速、病蟲害少，台灣全年皆可栽培", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8282", "official", "2026-08-19"),
    ("kongxincai", "種植方式", "撒播或條播，條播有利於日後採收", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8282", "official", "2026-08-19"),
    ("kongxincai", "發芽", "播種後一週內發芽，發芽後需盡快給予充足日照", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8282", "official", "2026-08-19"),
    ("kongxincai", "採收時機", "生長約20公分即可採收，越早採收枝條越嫩；每次採收後需補充肥料", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8282", "official", "2026-08-19"),
    ("kongxincai", "採收天數", "播種至採收約15～40天不等（依季節與栽培方式）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8282", "official", "2026-08-19"),
    ("kongxincai", "施肥", "有機質肥料施用量僅需佔培養土總體積10～20%", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8282", "official", "2026-08-19"),

    # 蘿蔔 - 農業知識入口網 knowledge_view id=8666（原文含中國大陸「畝/釐米」單位，套用台灣前需換算與交叉驗證，故標記qa）
    ("luobo", "適合季節", "秋冬蘿蔔品種為主，盛產期12月至翌年初春", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8666", "qa", "2026-08-19"),
    ("luobo", "育苗溫度", "10度以上", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8666", "qa", "2026-08-19"),
    ("luobo", "土壤條件", "土層深厚、疏鬆、排水良好、較肥沃之砂質壤土；避免十字花科蔬菜作前茬", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8666", "qa", "2026-08-19"),
    ("luobo", "種植方式", "點播或條播，點播窩距25～30公分，每窩點籽4～5粒", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8666", "qa", "2026-08-19"),
    ("luobo", "水分管理", "播種後乾旱時立即澆水；出苗時再澆水保持地面濕潤；多雨時須及時排水防止死苗", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8666", "qa", "2026-08-19"),
    ("luobo", "採收時機", "根部直徑膨大至8～10公分、長度25～30公分時採收較適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8666", "qa", "2026-08-19"),

    # 高麗菜（甘藍）- 農業知識入口網 甘藍主題館 subject id=13417（官方主題館頁面）
    ("gaolicai", "適合季節", "夏播3～4月，秋播高冷地7～9月，秋播平地9～11月", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),
    ("gaolicai", "適合溫度", "15～21℃", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),
    ("gaolicai", "土壤條件", "pH5.5～6.5，表土厚、排水良好之砂質壤土及黏質壤土較佳", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),
    ("gaolicai", "種植方式", "播種一個月後定植", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),
    ("gaolicai", "行株距", "50×120公分", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),
    ("gaolicai", "水分管理", "播種初期土壤須保持濕潤；生育初期早晚各噴水一次，中後期視天候每天噴水一次，於上午10時前實施、避免傍晚澆水", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),
    ("gaolicai", "採收天數", "夏播定植後60～85天，秋播定植後60～90天", "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13417", "official", "2026-08-19"),

    # 大白菜 - 農業知識入口網 knowledge_view id=2869（使用者問答，含中國大陸「畝」單位施肥資訊）
    ("dabaicai", "基肥（使用者分享）", "每畝腐熟有機肥3～5方、尿素9～11公斤、二銨15～20公斤或過磷酸鈣40～50公斤、氯化鉀或硫酸鉀15～20公斤", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2869", "qa", "2026-08-19"),
    ("dabaicai", "追肥（使用者分享）", "蓮座期每畝施尿素7～10公斤，包心期每畝施尿素20～30公斤", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2869", "qa", "2026-08-19"),
    ("dabaicai", "生育期病蟲害重點", "幼苗期防蚜蟲，蓮座期防治霜霉病，包心期防治軟腐病、炭疽病", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2869", "qa", "2026-08-19"),

    # 花椰菜 - 農業知識入口網（食農教育資訊整合平臺，官方）fae.moa.gov.tw
    ("huaqielan", "品種選擇（依季節）", "夏季栽培早生耐熱型，春秋季栽培中生或中晚生型，冬季栽培晚生耐寒型", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=106", "official", "2026-08-19"),
    ("huaqielan", "育苗", "以穴盤苗育苗，根團須完整，播種後30天苗齡為宜；秋冬季定植可用25天苗齡", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=106", "official", "2026-08-19"),
    ("huaqielan", "施肥", "定植後10天第1次追肥，之後每隔10天施1次，第3次約在定植後30～32天著蕾時施用；硼砂每公頃5公斤當基肥", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=106", "official", "2026-08-19"),
    ("huaqielan", "水分管理", "高溫乾旱季節需特別注意灌水，以溝灌方式為佳，灌滿水後應隨即排水", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=106", "official", "2026-08-19"),
    ("huaqielan", "採收", "花球發育至雞蛋大小（約5～6公分）時進行覆蓋，常需分數次採收，每天或隔日採收一次為佳", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=106", "official", "2026-08-19"),

    # 小黃瓜 - 農業知識入口網 knowledge_view id=7567
    ("xiaohuanggua", "適合季節", "播種期3～10月；另有早春栽培（12～2月）、秋季栽培（8～10月）、冬季栽培（10～12月）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7567", "official", "2026-08-19"),
    ("xiaohuanggua", "適合溫度", "生長適溫20～30℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7567", "official", "2026-08-19"),
    ("xiaohuanggua", "土壤條件", "需排水良好的土壤", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7567", "official", "2026-08-19"),
    ("xiaohuanggua", "種植方式", "種植前浸水2小時，覆土約1公分", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7567", "official", "2026-08-19"),
    ("xiaohuanggua", "植株管理", "真葉5片時立支柱引蔓，每一分枝留2葉摘心", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7567", "official", "2026-08-19"),
    ("xiaohuanggua", "施肥（原文含畝單位）", "定植後3～4天澆緩苗水，之後每隔5～7天澆尿素水溶液，每畝約10公斤；結瓜期每隔5～7天葉面噴施0.2～0.3%磷酸二氫鉀", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7567", "qa", "2026-08-19"),

    # 馬鈴薯 - 農業知識入口網 馬鈴薯主題館 subject id=52592（官方）+ 使用者問答 id=1946
    ("malingshu", "適合地區", "台中市、雲林及嘉義等地為發展成熟之產區，中南部地區冬裡作較適宜", "農業知識入口網（馬鈴薯主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=52592", "official", "2026-08-19"),
    ("malingshu", "適合溫度", "18～21℃", "農業知識入口網（馬鈴薯主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=52592", "official", "2026-08-19"),
    ("malingshu", "土壤條件", "沙質壤土或壤土，土質深厚", "農業知識入口網（馬鈴薯主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=52592", "official", "2026-08-19"),
    ("malingshu", "不適合地區原因", "北部因冬季多雨易發生晚疫病；高屏區冬季日溫仍高，影響生育和結薯", "農業知識入口網（馬鈴薯主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=52592", "official", "2026-08-19"),
    ("malingshu", "種薯準備（使用者分享）", "購買病菌檢驗合格種薯，約60公克、具1～2個芽；栽種前2～3天切成兩半，切口置陰涼處風乾", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1946", "qa", "2026-08-19"),
    ("malingshu", "種薯間隔（使用者分享）", "約30公分", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1946", "qa", "2026-08-19"),
    ("malingshu", "種植方式（使用者分享）", "種薯切口朝下，嫩芽位置在小溝中央，回填土壤約3～5公分後放入種薯，再覆蓋剩餘土壤", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1946", "qa", "2026-08-19"),
    ("malingshu", "水分與培土（使用者分享）", "土一乾就澆水；去芽並培土，花蕾變大兩週後進行第2次培土", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1946", "qa", "2026-08-19"),
    ("malingshu", "施肥（使用者分享）", "每一種薯需腐植質土300公克、化學肥料12公克；發育不良時每株追肥約5公克", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1946", "qa", "2026-08-19"),

    # 胡蘿蔔 - 農業知識入口網 knowledge_view id=8993
    ("huluobo", "適合季節", "秋季耕種冬季收穫；或反季節春天栽種夏天收穫", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8993", "qa", "2026-08-19"),
    ("huluobo", "適合溫度", "肉質根發育適溫18～23℃，發芽溫度20～25℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8993", "qa", "2026-08-19"),
    ("huluobo", "土壤條件", "適宜砂質土壤，保持土質疏鬆有利生長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8993", "qa", "2026-08-19"),
    ("huluobo", "株距", "每株距離10公分，每穴留一株", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8993", "qa", "2026-08-19"),
    ("huluobo", "水分管理", "前期不能施水過量以防地面部分生長過度；後期需供水充足使肉質根充分發育；採收前忌灌水", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8993", "qa", "2026-08-19"),
    ("huluobo", "中耕培土", "發芽後50天內輕度中耕培土；發芽後65～70天需培土至根肩處", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8993", "qa", "2026-08-19"),

    # 茄子 - 農業知識入口網 knowledge_view id=2847
    ("qiezi", "適合溫度", "幼苗期白天20～25℃、夜間17℃以上；15℃以下生長緩慢易落花，10℃以下停止生長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2847", "official", "2026-08-19"),
    ("qiezi", "水分管理", "約7天灌溉一次，畦面保持濕潤；過乾降低果實品質使果皮過硬，過濕易使根部腐爛", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2847", "official", "2026-08-19"),
    ("qiezi", "整枝摘葉", "定植後20～35天去除始花節位以下之葉片及蘗芽；始花期採雙幹或V型整枝；定植1個月後每株立1支柱", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2847", "official", "2026-08-19"),
    ("qiezi", "施肥", "基肥於整地前全圃撒施；追肥自開始採收後每7～10天施1次，冬天間隔長、夏天間隔短", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2847", "official", "2026-08-19"),
    ("qiezi", "採收時機", "茄果長達30公分以上、色澤亮麗、果實頂端撐開萼片時採收，約每2～3天採收一次，以清晨或傍晚為佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2847", "official", "2026-08-19"),

    # 甜椒 - 農業知識入口網 knowledge_view id=1623 + production_map id=41
    ("tianjiao", "適合季節", "秋作最適合；春夏之際多雨高濕、高溫栽培較困難，宜於高冷地栽培；冬作氣溫低且溫度不穩定", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1623", "official", "2026-08-19"),
    ("tianjiao", "適合溫度", "生育適溫22～30℃，果實生育最佳20～25℃，日溫最佳27℃、夜溫最佳20℃（夜溫低於15℃果實尾部會變尖）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1623", "official", "2026-08-19"),
    ("tianjiao", "土壤條件", "排水良好、肥沃的壤土，中性微酸土壤為宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1623", "official", "2026-08-19"),
    ("tianjiao", "種植方式與株距", "平地秋冬作：寬畦含畦溝150公分寬，雙行植行株距75×45公分；高冷地夏作：寬畦含畦溝120公分寬，單行植株距40公分", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1623", "official", "2026-08-19"),
    ("tianjiao", "施肥", "每十公畝施用2000公斤堆肥及100公斤43號複合肥料做基肥", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1623", "official", "2026-08-19"),
    ("tianjiao", "採收天數", "開花至轉色完全約需75天或更長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1623", "official", "2026-08-19"),
    ("tianjiao", "全國產期", "全年1～12月均有產出，產地含新竹、台中、彰化、南投、雲林、嘉義、高雄、屏東、台東等地", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=41", "official", "2026-08-19"),

    # 洋蔥 - 農業知識入口網 knowledge_view id=12924
    ("yangcong", "適合季節", "秋冬季到隔年春季，須選短日型品種因應台灣日照較短", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=12924", "official", "2026-08-19"),
    ("yangcong", "適合溫度", "種子發芽適溫16～25℃，根群發育適溫15～20℃，莖葉發育適溫20～26℃，生育最適溫度20～25℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=12924", "official", "2026-08-19"),
    ("yangcong", "土壤條件", "含豐富有機質的砂質壤土最好，pH值6.0～6.5最適合", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=12924", "official", "2026-08-19"),
    ("yangcong", "水分管理", "生長期需較濕潤環境，結球後期雨量不宜過多，採收前最怕下雨", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=12924", "official", "2026-08-19"),
    ("yangcong", "輪作建議", "不宜連作，適合與水稻、玉米等禾本科或豆科作物輪作", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=12924", "official", "2026-08-19"),

    # 絲瓜 - 農業知識入口網 絲瓜主題館 subject id=24754（官方，含北中南分區）
    ("sigua", "適合季節（北部）", "秋冬季溫度低而多雨，最適種植季節為春夏季", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),
    ("sigua", "適合季節（中部）", "主要種植於12～9月，尤其以農曆年（立春）前種植，6月間生產最多", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),
    ("sigua", "適合季節（南部）", "位處熱帶，周年均可栽培，但以秋冬季為主；冬季及早春低溫期由高屏地區供應全國所需", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),
    ("sigua", "株距", "秋冬季單蔓高密度栽培法株距30～60公分；農民慣行種植株距90～150公分", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),
    ("sigua", "定植與整枝", "幼苗定植成活後，葉齡4～5葉前早期摘心（春夏季留子蔓法）", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),
    ("sigua", "施肥", "基肥：堆肥20,000公斤/公頃、台肥39號及43號400～800公斤/公頃；追肥200～400公斤/公頃，雌花始花期後每隔7～10天施1次（始花前避免過量氮肥）", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),
    ("sigua", "採收天數", "雌花開花後高溫期10～12天、低溫期15～20天為採收適期，種皮未硬化前採收品質最佳", "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24754", "official", "2026-08-19"),

    # 四季豆 - 食農教育資訊整合平臺 fae.moa.gov.tw
    ("sijidou", "播種與株距", "每穴播種2～3粒，穴與穴距離30～60公分", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=119", "official", "2026-08-19"),
    ("sijidou", "水分管理", "播種前土壤須充分灌水再整地作畦，勿在乾燥土壤先播種再灌溉以避免種子腐爛；吸水性強，播種時應控制適當水分", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=119", "official", "2026-08-19"),
    ("sijidou", "支架時機", "花芽分化前（約長有4～8片葉開始抽蔓時）立好支架", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=119", "official", "2026-08-19"),
    ("sijidou", "採收天數", "圓莢型敏豆播種後40～60天可收穫，Kentucky wonder系需50～70天；落花後10～15天為採收適期，盛莢期每2～3天採收一次", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=119", "official", "2026-08-19"),

    # 芭樂 - 農業知識入口網 芭樂(番石榴)主題館 subject id=11873
    ("bale", "種植季節", "除豪雨季節外均可種植", "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11873", "official", "2026-08-19"),
    ("bale", "土壤條件", "以壤土為佳，微酸性土壤對果實品質有利；約70%根群分佈在土層30公分內", "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11873", "official", "2026-08-19"),
    ("bale", "株距", "株距3公尺，畦寬4～4.5公尺（含50公分排水溝）；每分地種植100株以上需進行間拔", "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11873", "official", "2026-08-19"),
    ("bale", "水分管理", "旱季約10～15天行濕潤噴灌一次，需注意排水設施", "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11873", "official", "2026-08-19"),
    ("bale", "施肥（5～6年樹齡參考）", "有機肥30公斤/株/年於4月一次施用；複肥43號1,300公克/株/年，分配4月30%、7～8月20%、10～2月50%，中強剪後開溝或穴施，施肥後濕潤灌溉", "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11873", "official", "2026-08-19"),
    ("bale", "定植季節", "容易積水的果園宜避免雨季定植；行距3.5～4.5公尺、株距2.7～3.6公尺", "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11730", "official", "2026-08-19"),

    # 菠菜 - 農業知識入口網 knowledge_view id=10653（通俗教學，qa等級）
    ("bocai", "適合季節", "全年均可種植，最好在秋天和冬天種植", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10653", "qa", "2026-08-19"),
    ("bocai", "土壤條件", "不適合酸性土壤", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10653", "qa", "2026-08-19"),
    ("bocai", "種植方式", "直接用種子播種育苗，播種前可先浸泡一天更容易發芽，約一週後開始發芽", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10653", "qa", "2026-08-19"),
    ("bocai", "施肥", "長出3～4片本葉後每2週施一次肥；長到4～5片真葉時間苗；採收後追施1次腐熟有機肥", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10653", "qa", "2026-08-19"),
    ("bocai", "水分管理", "生長期需充足水分，忌乾旱，一般每1～2天澆水1次，高溫時早晚各澆水以保持土壤濕潤", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10653", "qa", "2026-08-19"),

    # 茼蒿 - 農業知識入口網 knowledge_view id=8363
    ("tongao", "適合季節", "9月至翌年2月，3～8月因氣溫過高不適宜栽培", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),
    ("tongao", "發芽溫度", "15～20℃為最適宜發芽溫度，高溫發芽不良", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),
    ("tongao", "土壤條件", "最適pH為5.5～6.8", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),
    ("tongao", "整地施肥", "播種2週前每平方公尺施予2把苦土石灰，1週前施基肥，充分耕土20公分深", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),
    ("tongao", "間拔株距", "第一次間拔約3公分株間疏苗，第二次間拔10～15公分株間疏苗", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),
    ("tongao", "採收天數", "9～11月播種後25～30日可收穫；12月至翌年2月播種後30～50日可收穫", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),
    ("tongao", "採收方式", "10葉中摘取5～6葉，保留株底部4～5葉可重新長出側芽，可長期採收", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "official", "2026-08-19"),

    # 芥藍 - 農業知識入口網 knowledge_view id=18199（通俗教學，qa等級）
    ("jielan", "適合季節", "春季或秋季為最佳播種時間，喜涼爽氣候避免高溫", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "適合溫度", "最佳溫度15～20℃", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "土壤條件", "肥沃通氣土壤，混合腐葉土或堆肥，pH值6.0～7.0", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "種植方式與株距", "種子播撒於土表覆蓋0.5～1公分薄土，間苗保持每株10～15公分距離", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "水分管理", "保持土壤濕潤但避免積水，通常每週澆水1～2次，天氣炎熱時早晚各澆水一次", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "施肥", "每4～6週施一次平衡肥料，生長期每2～3週施一次稀釋液態肥", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "採收", "葉片長到15～20公分時即可開始收成", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),

    # 冬瓜 - 農業知識入口網 knowledge_view id=7146
    ("donggua", "摘心整枝（小果栽培）", "採收小果的栽培應於主蔓5～6葉時摘心，留4枝子蔓生長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7146", "official", "2026-08-19"),
    ("donggua", "摘心整枝（大果栽培）", "大冬瓜生產無須摘心，但側芽過多時宜用銳利剪刀「疏蔓」", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7146", "official", "2026-08-19"),
    ("donggua", "施肥", "植株與果實皆大，需充分養分，以化學肥料追肥約3～4次促進生育及著果", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7146", "official", "2026-08-19"),

    # 南瓜 - 農業知識入口網 南瓜主題館 subject id=29161（官方，含北中南分區）+ knowledge_view id=4006（通俗教學，qa）
    ("nangua", "適合季節（中南部）", "9、10月至翌年2月", "農業知識入口網（南瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29161", "official", "2026-08-19"),
    ("nangua", "適合季節（北部）", "3月播種最適宜", "農業知識入口網（南瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29161", "official", "2026-08-19"),
    ("nangua", "催芽溫度", "25～30℃", "農業知識入口網（南瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29161", "official", "2026-08-19"),
    ("nangua", "種植方式", "可採直播及穴盤育苗兩種方式，播種前需種子消毒、浸泡5～10小時、清洗及催芽", "農業知識入口網（南瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29161", "official", "2026-08-19"),
    ("nangua", "採收天數（使用者分享）", "生長期視品種大小而定，一般需三個月以上", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4006", "qa", "2026-08-19"),
    ("nangua", "人工授粉（使用者分享）", "最佳時間為清晨5～6點；開花期需注意授粉並在根部加肥料", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4006", "qa", "2026-08-19"),

    # 苦瓜 - 農業知識入口網 苦瓜主題館 subject id=38098（官方，含北中南分區）
    ("kugua", "適合季節（北部）", "3～6月", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "適合季節（中部）", "2～9月", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "適合季節（南部）", "全年可栽培，冬季需選耐寒品種", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "催芽", "45℃溫水浸種12～24小時，催芽環境30℃", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "土壤條件", "砂質至黏質壤土，pH5.5～6.5最適合，排水需良好、較鬆軟", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "種植方式與株距", "畦寬4～5公尺，拱形/三角隧道式/水平式棚架；苗株約60公分摘心留3～6條子蔓；株距1.5～2.5公尺打洞定植", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "水分管理", "育苗期介質保持濕潤、乾濕變化不可過大；定植後每日早晚澆灌或點灌，成活後改溝灌", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),
    ("kugua", "施肥", "基肥腐熟堆肥12,000公斤/公頃以上；追肥撒施於根基部約10公分處", "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38098", "official", "2026-08-19"),

    # A菜（萵苣）- 農業知識入口網 萵苣主題館 subject id=8568
    ("azhai", "適合季節（葉萵苣）", "週年皆可栽植，以四月上旬至八月下旬較適", "農業知識入口網（萵苣主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=8568", "official", "2026-08-19"),
    ("azhai", "適合季節（嫩莖萵苣）", "南部9～2月中旬，中部9～2月，北部8～2月，高冷地3～8月", "農業知識入口網（萵苣主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=8568", "official", "2026-08-19"),
    ("azhai", "株距", "結球萵苣行株距40～45×25～30公分；嫩莖萵苣60～75×30～35公分；葉萵苣間拔成行株距10×10公分", "農業知識入口網（萵苣主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=8568", "official", "2026-08-19"),
    ("azhai", "採收天數", "葉萵苣約35～45天；結球萵苣定植後40～45天；嫩莖萵苣定植後45～60天", "農業知識入口網（萵苣主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=8568", "official", "2026-08-19"),

    # 芋頭 - 農業知識入口網 knowledge_view id=9168（通俗教學，qa等級）+ 病蟲害主題館 subject id=18996（官方）
    ("yutou", "適合季節（使用者分享）", "種植時間春節前後，約2月；採收期秋天（9月以後）至春節前", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9168", "qa", "2026-08-19"),
    ("yutou", "種植方式（使用者分享）", "選擇細長形小芋頭做種苗，長出小苗約30公分時，選最凹處或斜面下方種植，建議淹水灌溉", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9168", "qa", "2026-08-19"),
    ("yutou", "覆土（使用者分享）", "4、5、6月各覆土一次，可同時除草", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9168", "qa", "2026-08-19"),
    ("yutou", "採收時機（使用者分享）", "快恢復到芋苗大小時採收（秋天後期）；採收前保持土壤乾燥；春節前需全部採收完畢否則會空心；水芋生長週期8～9個月，旱芋10個月", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9168", "qa", "2026-08-19"),

    # 薑 - 農業知識入口網 knowledge_view id=4362
    ("jiang", "適合季節", "北部2～4月，中南部12～4月，山地可利用3～4月雨期種植", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4362", "official", "2026-08-19"),
    ("jiang", "適合溫度", "18℃即可萌芽，25～32℃為生育最適溫度，15℃為生育低限溫度，塊莖10℃以下容易腐敗", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4362", "official", "2026-08-19"),
    ("jiang", "土壤條件", "富含有機質具保水力之壤土或黏質壤土較適宜；生產老薑多選適濕砂壤土之山坡地", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4362", "official", "2026-08-19"),
    ("jiang", "水分管理", "喜好濕潤，水分缺乏塊莖停止肥大；易乾旱土地栽培需有灌溉設施", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4362", "official", "2026-08-19"),
    ("jiang", "輪作建議", "忌連作，同一塊地必須改種其他作物5～6年", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4362", "official", "2026-08-19"),

    # 豌豆 - 農業知識入口網 豌豆主題館 subject id=38915
    ("wandou", "適合季節", "平地播種期8月下旬至翌年1月下旬；高冷地夏季栽培可於2～8月播種；過早播種易遇高溫使植株衰弱、產量減少、品質下降", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38915", "official", "2026-08-19"),
    ("wandou", "畦寬與株距", "畦寬(連畦溝)1.5～1.8公尺兩行植，或1.2公尺種一行；行株距以40公分為基準，條播粒距約3公分；種子用量每分地3～6公斤", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38915", "official", "2026-08-19"),
    ("wandou", "排水", "排水良好土地畦高10～15公分；排水較差土地建議做20～30公分高畦", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38915", "official", "2026-08-19"),
    ("wandou", "施肥", "苗期需施用足量氮肥，開花結莢後繼續供氮可提高產量", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38915", "official", "2026-08-19"),
    ("wandou", "水分管理", "結莢期間可減少灌溉次數，土壤水分太充足易促進莖葉生長而不利結莢", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38915", "official", "2026-08-19"),
    ("wandou", "採收天數", "嫩莢豌豆早生品種播種後60天、中生70天；甜豌豆早生70天、中生80天、晚生90天；豌豆苗播種後30～40天開始採收", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38915", "official", "2026-08-19"),

    # 毛豆 - 農業知識入口網（農產品產期產地）theme_data production_map id=154
    ("maodou", "全國產期", "2、3、4、9、10、11月", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=154", "official", "2026-08-19"),
    ("maodou", "採收標準", "八分飽滿時採收，此時豆莢仍翠綠且外有茸毛", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=154", "official", "2026-08-19"),
    ("maodou", "主要產地", "屏東縣（崁頂鄉，種植面積最大3,783.89公頃）、雲林縣（2,400.86公頃）、彰化縣（62.99公頃）", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=154", "official", "2026-08-19"),

    # 柑橘 - 農業知識入口網 柑橘主題館 subject id=6177
    ("ganju", "各品種產期", "檸檬/萊姆全年生產；麻豆文旦8月下旬起採收；椪柑10月起上市；柳橙11月起採收；桶柑/茂谷柑2月起上市；晚崙西亞3、4月上市", "農業知識入口網（柑橘主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=6177", "official", "2026-08-19"),
    ("ganju", "各品種主要產地", "椪柑：苗栗/台中/雲林/嘉義/台南；柳橙：南投/雲林/嘉義/台南；桶柑：宜蘭/新竹/苗栗/台中/花蓮/台東；麻豆文旦：花蓮/台南/苗栗/宜蘭；檸檬：屏東；海梨柑：新竹特產；金柑：宜蘭特產；白柚：台南/台東/嘉義；晚崙西亞：台東特產", "農業知識入口網（柑橘主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=6177", "official", "2026-08-19"),

    # 芒果 - 農業知識入口網 芒果主題館 subject id=10690
    ("mangguo", "生育週期（屏東）", "6～7月開始抽梢，9～10月停梢，開花著果期12～2月", "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=10690", "official", "2026-08-19"),
    ("mangguo", "生育週期（高雄、台南以北）", "7～8月抽梢，10～11月停梢，開花著果期2～3月", "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=10690", "official", "2026-08-19"),
    ("mangguo", "開花著果期長度", "自花序抽長後起維持約45天，花期後約1個月進入結果期", "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=10690", "official", "2026-08-19"),
    ("mangguo", "採收期（依品種）", "土芒果約6月之前；愛文/玉文/金煌/夏雪/蜜雪5月(屏東)至7月(台南)；慢愛文/聖心/蘋果文7月底至8月；凱特/紅凱特8～9月；四季芒果6～7月(未調節)或11～2月(經產期調節)", "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=10690", "official", "2026-08-19"),
    ("mangguo", "苗木定植適期", "3～10月均可進行，應避免連續雨季及颱風天定植；冬季（尤其寒流期間）苗木處於停梢狀態，種植後不易長新根，應避免冬季定植", "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=10855", "official", "2026-08-19"),
    ("mangguo", "定植方式", "植穴長寬深各約50公分，表土底土分開回填並施有機質肥料及少許化肥當基肥；種植深度以根頸與地面平行為準，定植後需澆水直至成活", "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=10855", "official", "2026-08-19"),

    # 木瓜 - 農業知識入口網 knowledge_view id=511
    ("mugua", "土壤條件", "對土壤要求不嚴、適應性強，以土質肥沃、水源充足、排水便利為宜；不可種在會積水或淹水的地方", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=511", "official", "2026-08-19"),
    ("mugua", "種植方式", "採用種子育苗或扦插成苗後移栽，生長3～5年後開花結果；需種植兩性株才有利結果，雌性株需人工授粉", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=511", "official", "2026-08-19"),
    ("mugua", "株距", "1～1.2公尺", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=511", "official", "2026-08-19"),
    ("mugua", "施肥", "施磷肥促進開花，施肥位置離根部遠一點；建議分東西南北四區輪流施肥避免過量肥料傷害", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=511", "official", "2026-08-19"),
    ("mugua", "定植適期", "春植(2～3月)或秋植(9～11月)最適合，秋植較易成功；全年皆可定植，月份僅表示生育階段時間，開花結果期及成熟採收期為連續性", "食農教育資訊整合平臺", "https://fae.moa.gov.tw/map/food_item.php?type=AS04&id=51", "official", "2026-08-19"),

    # 鳳梨 - 農業知識入口網 鳳梨主題館 subject id=5967
    ("fengli", "種植時間換算", "種植時間需依目標採收月份反推，例如欲翌年4月採收（台農17號）則於前一年10月種植；早春定植僅能用冠芽及吸芽繁殖，年底種植則冠芽/裔芽/吸芽皆可用", "農業知識入口網（鳳梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=5967", "official", "2026-08-19"),
    ("fengli", "種植密度", "二列式三角形密植，每公頃3萬5,000至4萬株苗；畦距約100公分，行距約50公分，株距36～30公分", "農業知識入口網（鳳梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=5967", "official", "2026-08-19"),

    # 蓮霧 - 農業知識入口網 knowledge_view id=62
    ("lianwu", "苗木定植季節", "2～3月或10～11月為宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=62", "official", "2026-08-19"),
    ("lianwu", "適合溫度", "性喜溫暖怕寒冷，遇10℃以下低溫易造成寒害", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=62", "official", "2026-08-19"),
    ("lianwu", "土壤條件", "壤土果園保肥力佳、成本低，較易控制植株徒長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=62", "official", "2026-08-19"),
    ("lianwu", "種植方式與株距", "寬行栽植，行距7～8公尺，株距5.5公尺", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=62", "official", "2026-08-19"),
    ("lianwu", "生長特性", "生長勢強，每年抽新梢6～7次，每次間隔依溫度而定需50～60天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=62", "official", "2026-08-19"),
    ("lianwu", "施肥", "採收後給予「禮肥」；整枝修剪期間給予基肥；開花著果後給予追肥", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=62", "official", "2026-08-19"),

    # 玉米 - 農業知識入口網 knowledge_view id=3581
    ("yumi", "適合季節（南部）", "1月下旬～3月中旬、9月上中旬（兩次產期）；超甜玉米適播期9月上旬至10月上旬", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3581", "official", "2026-08-19"),
    ("yumi", "株距與播種量", "行株距80×25公分，每公頃播種量15公斤", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3581", "official", "2026-08-19"),
    ("yumi", "成熟期", "約70天左右，成熟標誌為玉米穗上的鬚變黑變微乾；一株只留一穗最佳，採收後植株不會再長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3581", "official", "2026-08-19"),

    # 地瓜（甘藷）- 農業知識入口網 甘藷主題館 subject id=19318
    ("digua", "適合季節（南部）", "插植適期8～9月", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19318", "official", "2026-08-19"),
    ("digua", "適合季節（中北東部）", "插植適期3～4月或6～8月", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19318", "official", "2026-08-19"),
    ("digua", "各期作", "春作：種植1～4月、收穫6～10月；夏作：種植5～7月、收穫11～12月；秋作及晚秋作：種植8～11月、收穫翌年1～5月", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19318", "official", "2026-08-19"),
    ("digua", "種植方式", "以水平淺植法最理想，或行斜植法，藷苗先端應直立", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19318", "official", "2026-08-19"),
    ("digua", "株距", "行距110～120公分、株距25～30公分；或標準規格100×25公分", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19318", "official", "2026-08-19"),

    # 香蕉 - 農業知識入口網 香蕉主題館 subject id=11046
    ("xiangjiao", "種植方式", "正方形種植、三角形種植、寬窄行種植三種方式", "農業知識入口網（香蕉主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11046", "official", "2026-08-19"),
    ("xiangjiao", "種植密度與株距", "每公頃1,800～2,000株；行株距約2.4×2.1公尺，或寬窄行3.6×1.6×1.6公尺三角形高畦", "農業知識入口網（香蕉主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11046", "official", "2026-08-19"),
    ("xiangjiao", "整地", "排水不良處應先作高畦；挖深度約20～30公分穴種植，使苗的塊莖深入土中", "農業知識入口網（香蕉主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11046", "official", "2026-08-19"),

    # 青花菜（實為花椰菜資料，標記警示）
    ("lvhuaqielan", "⚠️品種播種適期（此為花椰菜資料非青花菜專屬）", "早生品種7～9月播種育苗，中生品種9～10月，晚生品種10～12月", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=30125", "qa", "2026-08-19"),

    # 韭菜 - 農業知識入口網 knowledge_view id=9436 + 花蓮區農改場施肥技術
    ("jiucai", "適合季節", "播種適期11月至翌年3月，分株法適期11～12月；台灣目前全年均可栽培，但以冬春季品質較佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9436", "official", "2026-08-19"),
    ("jiucai", "適合溫度", "生育適溫15～25℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9436", "official", "2026-08-19"),
    ("jiucai", "採收週期", "播種後約4個月可第1次採收；割取地上切口後再培育40天左右可再收割，可循環採收多次", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9436", "official", "2026-08-19"),
    ("jiucai", "施肥（花蓮區農改場）", "合理化施肥搭配有機質肥料及有益微生物菌，可降低肥料用量、降低病蟲發生率並提高品質，每公頃約可降低肥料成本6,500元", "農業知識入口網（花蓮區農改場）", "https://kmweb.moa.gov.tw/theme_data.php?theme=news&sub_theme=agri_life&id=53794", "official", "2026-08-19"),

    # 蔥 - 農業知識入口網 knowledge_view id=1498
    ("cong", "適合季節", "種植時期以8～10月播種為佳；北蔥全年均可種植，但以夏後為佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),
    ("cong", "適合溫度", "種子發芽溫度範圍廣，以15～30℃最適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),
    ("cong", "土壤條件", "黏質壤土最佳，土層須深厚，保水及排水良好，pH以5.7～7.4為宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),
    ("cong", "種植方式與株距", "播種法條播，以18～20公分齒距耙成條溝，發芽後間拔至株距4～5公分；定植株距12～15公分", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),
    ("cong", "水分管理", "根部非常怕浸水，約1～2日澆水一次並注意排水", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),
    ("cong", "施肥", "定植後每隔約20日施追肥一次，共約四次", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),
    ("cong", "採收天數", "分株法約需90天；種子法約需270天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1498", "official", "2026-08-19"),

    # 大蒜 - 農業知識入口網 大蒜主題館 subject id=57437
    ("dasuan", "適合季節", "國曆9～12月均可播種；蒜頭栽培宜9月中旬至10月中旬播種", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57437", "official", "2026-08-19"),
    ("dasuan", "土壤與整地", "需疏鬆土壤，作15～20公分高畦種植，畦寬60～120公分種2～4行", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57437", "official", "2026-08-19"),
    ("dasuan", "種植密度與株距", "行距15～20公分、株距8～10公分；每公頃320,000～400,000株，種蒜用量1,000～1,300公斤蒜瓣；播種深度3～4公分", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57437", "official", "2026-08-19"),
    ("dasuan", "水分管理", "初期(40天內)約5～7天灌水一次；中期(40～80天)約10～15天灌水一次；肥大初期(80～120天)約隔20天灌溉一次；肥大末期至成熟應停止灌水", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57437", "official", "2026-08-19"),
    ("dasuan", "施肥", "青蒜：播種後70天內分3次施用；蒜頭：90天內分3～4次施用", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57437", "official", "2026-08-19"),
    ("dasuan", "採收天數", "青蒜播種後80～100天；蒜球播植後約5個月，採收時地上莖葉有1/3至2/3黃萎", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57437", "official", "2026-08-19"),

    # 西瓜 - 農業知識入口網 knowledge_view id=3863 + production_map id=26
    ("xigua", "適合溫度", "種子發芽適溫26～30℃，莖葉發育適溫24～30℃，果實發育成熟需28～32℃；生長適溫25～30℃，6～10℃易受寒害", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3863", "official", "2026-08-19"),
    ("xigua", "地理條件", "月平均氣溫19℃以上的月份全年多於3個月的地區才可行露地栽培；台灣南部冬季氣溫仍適合栽種，深冬寒流時用稻草防寒可度過幼苗期並於初春採收", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3863", "official", "2026-08-19"),
    ("xigua", "植物特性", "屬長日照植物，喜強光，適宜乾熱氣候，耐旱力強", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3863", "official", "2026-08-19"),
    ("xigua", "全國產期與產地", "產期3～11月；產地含宜蘭大同、桃園觀音、苗栗後龍、彰化二林、雲林多鄉鎮、嘉義義竹、台南麻豆善化、高雄路竹阿蓮、花蓮鳳林壽豐玉里瑞穗", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=26", "official", "2026-08-19"),

    # 芥菜 - 農業知識入口網 knowledge_view id=1497
    ("jiecai", "適合季節與溫度", "主要栽培期為秋冬季，適合溫度16～22℃間生育最旺盛，日夜溫差大時品質最佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "official", "2026-08-19"),
    ("jiecai", "土壤條件", "砂質土，土層深厚，排水良好，pH值約5左右為適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "official", "2026-08-19"),
    ("jiecai", "種植方式", "先用穴盤栽種，一穴一種子，發芽後一穴一苗，再移植到田間", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "official", "2026-08-19"),
    ("jiecai", "水分管理", "不缺水即可適應，水分過多會使肉質莖與根腐爛", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "official", "2026-08-19"),
    ("jiecai", "施肥", "有機質肥料每公頃施用1～1.5公噸加台肥5號800公斤；缺硼時用0.4%硼砂水溶液葉面施肥", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "official", "2026-08-19"),

    # 油菜 - 農業知識入口網 knowledgebase id=282792
    ("youcai", "適合溫度", "發芽適溫20～25℃，生育適溫15～20℃，生長初期喜溫暖濕潤", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=13229&keyword=&id=282792", "official", "2026-08-19"),
    ("youcai", "土壤條件", "對土壤選擇不嚴，pH值5～8左右、排水良好且肥沃的土壤最適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=13229&keyword=&id=282792", "official", "2026-08-19"),
    ("youcai", "播種量", "每公頃約需種子6～9公斤", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=13229&keyword=&id=282792", "official", "2026-08-19"),
    ("youcai", "產期（台東地區）", "二期稻作收穫後(11月下旬)至立春(2月上旬)為種植生長期，開花期約45天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=13229&keyword=&id=282792", "official", "2026-08-19"),

    # 荔枝 - 農業知識入口網 荔枝主題館 subject id=24091
    ("lizhi", "適合定植季節", "2～4月及10～11月為較適宜的定植期", "農業知識入口網（荔枝主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24091", "official", "2026-08-19"),
    ("lizhi", "株距", "採4×3公尺或4×4公尺行株距，亦建議可用5×5公尺", "農業知識入口網（荔枝主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24091", "official", "2026-08-19"),
    ("lizhi", "定植方式", "植穴30公分寬、30公分深，可混合完全腐熟牛糞堆肥3公斤，土壤回填需超過苗根圈上端10公分", "農業知識入口網（荔枝主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24091", "official", "2026-08-19"),
    ("lizhi", "定植後灌溉", "初期2個月密集灌溉每1～2天一次；第二次新梢成熟後可隔3天灌溉一次，維持1年", "農業知識入口網（荔枝主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24091", "official", "2026-08-19"),
    ("lizhi", "施肥時機", "定植時不可用化學肥料，需待第三次新梢生長後才能使用", "農業知識入口網（荔枝主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24091", "official", "2026-08-19"),
    ("lizhi", "全台產期（依地區）", "高屏地區最早5月初成熟；嘉南地區6月初；南投台中地區6月中下旬；新竹地區7月中上旬；中海拔山區（300-400公尺）8月初", "農業知識入口網（荔枝主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24000", "official", "2026-08-19"),

    # 龍眼 - 農業知識入口網 龍眼主題館 subject id=44974
    ("longyan", "嫁接繁殖", "主要嫁接期1～3月，常用切接法，嫁接後氣溫回暖使根部枝梢開始活動生長，成活率高可縮短幼年期", "農業知識入口網（龍眼主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=44974", "official", "2026-08-19"),
    ("longyan", "高壓繁殖", "全年皆可進行，選適當枝條環剝後包覆水苔等保水介質，成活率高且保持原品種特性；但根系較淺分散，定植初期遇颱風較易傾倒", "農業知識入口網（龍眼主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=44974", "official", "2026-08-19"),
    ("longyan", "種子繁殖", "種子屬異儲型不耐乾燥，取出後需盡快播種，繁殖後代常需6年以上才開花結果，主要用於嫁接砧木培育或育種", "農業知識入口網（龍眼主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=44974", "official", "2026-08-19"),
    ("longyan", "花芽分化", "分化期約12月至1月，結果母枝需感受15～22℃涼溫持續8～10週，頂端休眠芽才由葉芽轉為花芽", "農業知識入口網（龍眼主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=44982", "official", "2026-08-19"),
    ("longyan", "採收適期", "果皮由青色轉淡褐色、粗糙轉光滑、輕壓有彈性即為採收適期；過早風味未達最佳，過晚甜度下降（俗稱「退甘」）", "農業知識入口網（龍眼主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=44985", "official", "2026-08-19"),

    # 百香果 - 農業知識入口網 百香果主題館 subject id=40148/40168
    ("baixiangguo", "播種適期", "一年四季皆可播種，在台灣以8、9月或2、3月最合適；種子需浸水發酵不超過3天，播種後約10～14天發芽", "農業知識入口網（百香果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40168", "official", "2026-08-19"),
    ("baixiangguo", "扦插繁殖", "全年可進行，以3～4月與9～10月最合適，利用去年生成熟枝條，約30天後可長根", "農業知識入口網（百香果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40168", "official", "2026-08-19"),
    ("baixiangguo", "定植與開花結果", "更新定植時間大多於2～3月（集中元宵節前後）；第一批花約5月開放，著果後55～60天成熟自然掉落", "農業知識入口網（百香果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40148", "official", "2026-08-19"),
    ("baixiangguo", "產期", "正常期作採收落於盛夏7月，可持續採收至隔年春節前；設施栽培結合冬季電照技術可使產期集中於當年7月至隔年2月", "農業知識入口網（百香果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40148", "official", "2026-08-19"),

    # 火龍果 - 農業知識入口網 knowledge_view id=3483
    ("huolongguo", "土壤條件", "含腐殖質多、保水保肥的中性或弱酸性土壤為好；含沙率40～70%的通風透光坡地佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3483", "official", "2026-08-19"),
    ("huolongguo", "適合溫度", "最佳適宜溫度20～30℃；北方種植須建溫室大棚，冬季夜間溫度不低於8℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3483", "official", "2026-08-19"),
    ("huolongguo", "種植方式與株距", "柱式栽培為主，每柱周圍種4株苗，畝栽300～400株，柱高2米水泥柱作支架", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3483", "official", "2026-08-19"),
    ("huolongguo", "施肥", "苗期施薄肥，每7～10天施一次複合肥", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3483", "official", "2026-08-19"),

    # 山藥 - 農業知識入口網 保健植物(香藥草)主題館 subject id=17915
    ("shanyao", "適合季節", "無性繁殖於清明節前後或2～4月間進行；塊莖生長發育於11～12月達最高峰", "農業知識入口網（保健植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=17915", "official", "2026-08-19"),
    ("shanyao", "適合溫度", "種薯發芽適溫約17～18℃，莖蔓生長適溫約25～26℃，新薯塊發育適溫約22～23℃", "農業知識入口網（保健植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=17915", "official", "2026-08-19"),
    ("shanyao", "土壤條件", "宜疏鬆、深厚且排水良好，以富含有機質的砂質壤土較宜", "農業知識入口網（保健植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=17915", "official", "2026-08-19"),
    ("shanyao", "種植方式", "分一般種植及塑膠穴管(天溝)誘導栽培兩種，建議採用塑膠穴管誘導栽培", "農業知識入口網（保健植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=17915", "official", "2026-08-19"),
    ("shanyao", "株距", "定植株距約30公分，行距100～150公分", "農業知識入口網（保健植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=17915", "official", "2026-08-19"),
    ("shanyao", "降雨量適應範圍", "600～3,000毫米降雨量地區均可栽植", "農業知識入口網（保健植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=17915", "official", "2026-08-19"),

    # 牛蒡（通俗種植教學，qa等級）
    ("niupang", "適合季節", "春初2～3月播種，也可初秋7～8月播種；直播或移栽後第二年秋季採收", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=115", "qa", "2026-08-19"),
    ("niupang", "土壤條件", "對土壤要求不嚴，宜選土層深厚、疏鬆、排水良好的地塊", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=115", "qa", "2026-08-19"),

    # 蘆筍 - 農業知識入口網 蘆筍主題館 subject id=30093
    ("lusun", "適合季節（田間苗）", "春季3月下旬至4月上旬（最適宜）、秋季10月上旬至11月中旬；應避免6～8月高溫多雨定植", "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30093", "official", "2026-08-19"),
    ("lusun", "適合季節（穴盤苗）", "任何季節皆可定植，但須避開颱風期，建議颱風期過後9～10月間種植", "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30093", "official", "2026-08-19"),
    ("lusun", "株距", "定植行株距150×20公分", "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30093", "official", "2026-08-19"),
    ("lusun", "苗木條件", "幼苗高度約15～20公分（播種後1.5～2個月），需至少有3支地上莖之幼苗才適於栽植", "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30093", "official", "2026-08-19"),

    # 茭白筍 - 農業知識入口網 茭白筍主題館 subject id=60494
    ("jiaobaisun", "適合溫度", "生育初期溫度15～20℃，嫩莖發育溫度20～30℃；溫度低於10℃或高於30℃都不利於孕茭", "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=60494", "official", "2026-08-19"),
    ("jiaobaisun", "土壤條件", "水源豐富、排水良好、富含有機質的黏質壤土為佳，pH5.5～6.5，不適合鹼性土壤", "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=60494", "official", "2026-08-19"),
    ("jiaobaisun", "種植方式", "以留母莖分株法無性繁殖，種植深度約5～10公分，以不被流水浮起為原則", "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=60494", "official", "2026-08-19"),
    ("jiaobaisun", "株距", "1×1公尺每分地約1,000株；1.3×1.3公尺每分地約600株", "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=60494", "official", "2026-08-19"),
    ("jiaobaisun", "水分管理", "初期保持3～5公分水深促進發根與分蘗；採收期宜高水位（水深40公分以上），水源應為流動水", "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=60494", "official", "2026-08-19"),

    # 紅豆 - 農業知識入口網 紅豆主題館 subject id=39708
    ("hongdou", "生育期天數", "播種至始花期32～40天，播種至成熟平均90天；花期維持25～30天", "農業知識入口網（紅豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39708", "official", "2026-08-19"),
    ("hongdou", "種植密度", "每0.1公頃栽培密度平均約40,000～45,000株", "農業知識入口網（紅豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39708", "official", "2026-08-19"),
    ("hongdou", "植株特性", "分枝著生於主莖第3～5節葉腋間，植株生長至8～10個複葉時開花", "農業知識入口網（紅豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39708", "official", "2026-08-19"),

    # 花生 - 農業知識入口網 knowledge_view id=13048
    ("huasheng", "生育日數", "春作生育日數約120～150天，秋作約100～120天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13048", "official", "2026-08-19"),
    ("huasheng", "始花期", "春作播種後至始花期約30～35天，秋作約21～24天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13048", "official", "2026-08-19"),
    ("huasheng", "採收季節", "台灣每年可收成兩次，農曆5～7月採收稱「春豆」（成長期約4個月），農曆10～12月採收稱「冬豆」（成長期約4個月）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13048", "official", "2026-08-19"),
    ("huasheng", "採收判斷", "豆莢種皮大部分呈淡粉紅色時即可考慮採收", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13048", "official", "2026-08-19"),

    # 葡萄 - 農業知識入口網 葡萄主題館 subject id=18142
    ("putao", "一年二收模式（第一收）", "2～3月進行冬季修剪，7～8月採收第一收果實", "農業知識入口網（葡萄主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18142", "official", "2026-08-19"),
    ("putao", "一年二收模式（第二收）", "第一收後修剪萌發夏梢，12～1月間採收第二收果實", "農業知識入口網（葡萄主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18142", "official", "2026-08-19"),
    ("putao", "南投竹山示例", "12月第一次修剪，5月第一收採收；第一收後第二次修剪，10月第二收採收", "農業知識入口網（葡萄主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18142", "official", "2026-08-19"),

    # 草莓 - 農業知識入口網 knowledge_view id=1229
    ("caomei", "適合季節", "栽培繁殖季節為秋冬春3季；定植於9月底至10月中旬（走莖小苗健康選種後定植）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1229", "official", "2026-08-19"),
    ("caomei", "適合溫度", "種植適溫15～25℃，喜冷涼氣候", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1229", "official", "2026-08-19"),
    ("caomei", "土壤條件", "富含有機質之肥沃或砂質土壤為佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1229", "official", "2026-08-19"),
    ("caomei", "種植方式", "以走莖繁殖，利用走莖上的小苗定植；淺根性根系，建議第二年採收後剷除重新種植", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1229", "official", "2026-08-19"),
    ("caomei", "採收天數", "開花受粉後果實成熟約需30～60天，依氣溫、品種而異", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1229", "official", "2026-08-19"),
    ("caomei", "覆蓋管理", "以銀黑兩面塑膠布覆蓋，黑面朝下抑制雜草，銀面朝上反射日照促進光合作用", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1229", "official", "2026-08-19"),

    # 秋葵 - 農業知識入口網 knowledge_view id=2345
    ("qiukui", "適合季節", "春作3～4月間播種，秋作8～9月間播種；播種不可太遲，遇寒流會嚴重影響產量", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2345", "official", "2026-08-19"),
    ("qiukui", "種植方式", "72孔穴盤裝泥炭土介質，種子挖約1公分深小洞播種，約3天發苗，植株長到6公厘左右移植到田間", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2345", "official", "2026-08-19"),
    ("qiukui", "株距", "約2呎（約60公分）距離種一株", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2345", "official", "2026-08-19"),
    ("qiukui", "採收時機", "果實約10～15公分為最佳賞味期，採收時果實表面有小刺需戴手套", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2345", "official", "2026-08-19"),

    # 皇宮菜（落葵）- 通俗種植教學，qa等級
    ("huanggongcai", "種植方式", "摘取約10公分頂芽扦插繁殖，約1週長根，環境需陰處但有日光照射，保持通風及土壤排水", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4727", "qa", "2026-08-19"),
    ("huanggongcai", "水分管理", "耐旱但需穩定充足給水才能正常生長，忌土壤太濕或浸水，容易腐爛", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13106", "qa", "2026-08-19"),
    ("huanggongcai", "施肥", "盛產期(4～10月)每2週施含氮量高之複合肥料補充養分", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13106", "qa", "2026-08-19"),

    # 九層塔 - 通俗種植教學，qa等級
    ("jiucengta", "適合季節", "全年均可栽種，5～10月最佳，高溫是發芽及生長必要條件，5月中旬後播種最理想", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9098", "qa", "2026-08-19"),
    ("jiucengta", "光照與土壤", "需至少6～8小時直射陽光，適應性強在20℃以上易栽培；選排水良好、富含有機質土壤", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=17802", "qa", "2026-08-19"),
    ("jiucengta", "水分管理", "幼苗易發生「濕腐」，需控制澆水量避免過濕，建議上午澆水、切忌傍晚澆水", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=17802", "qa", "2026-08-19"),
    ("jiucengta", "採收方式", "主幹長到20～30公分時可摘芯採收，宜隨時摘除花穗促進分枝；平均採收約需40天", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9098", "qa", "2026-08-19"),

    # 香菜（芫荽）- 通俗種植教學，qa等級
    ("xiangcai", "適合季節與溫度", "生長適溫15～18℃，30℃以上停止生長，台灣以春、秋、冬季較適合種植", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8800", "qa", "2026-08-19"),
    ("xiangcai", "播種前處理", "種皮較堅硬播種前應搓開利於出芽；夏季栽培需浸種24小時後濕布包好置於20℃環境催芽3～4天至露白", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8800", "qa", "2026-08-19"),
    ("xiangcai", "水分管理", "幼苗期3～4天澆水一次；生長旺盛期需加強水肥管理保持土面濕潤", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8800", "qa", "2026-08-19"),
    ("xiangcai", "採收時機", "出土30～50天、苗高15～20公分時即可間拔採收", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8800", "qa", "2026-08-19"),

    # 蓮藕 - 農業知識入口網 knowledgebase id=20787
    ("lianou", "適合季節（南部）", "3月上旬開始生長進入浮葉期，栽培適期2月中旬至4月中旬", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=0&type=12821&id=20787", "official", "2026-08-19"),
    ("lianou", "適合季節（北部）", "較南部約晚2～3星期，栽培適期3月中旬至4月下旬", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=0&type=12821&id=20787", "official", "2026-08-19"),
    ("lianou", "適合溫度", "萌芽始溫約18℃以上，生長適溫26～30℃，秋天低於22℃開花受抑制", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=0&type=12821&id=20787", "official", "2026-08-19"),
    ("lianou", "種植密度", "每公頃種藕需求量約1,000～1,200塊（約500公斤），種藕大多二節且具二葉", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=0&type=12821&id=20787", "official", "2026-08-19"),
    ("lianou", "採收時機", "根莖栽植後約120～150天充實；南部2～4月定植者6～8月可採收，北部約晚1個月；早熟品種結藕於7月上旬，中晚熟品種7月下旬或8月上旬", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=0&type=12821&id=20787", "official", "2026-08-19"),

    # 楊桃 - 農業知識入口網
    ("yangtao", "生長環境", "以北迴歸線以南、不易有寒害地區栽植較適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6519", "official", "2026-08-19"),
    ("yangtao", "結果時間", "嫁接苗約9個月後開始著果；定植苗2～3年後開花結果；種子播種結果時間更長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6519", "official", "2026-08-19"),
    ("yangtao", "全國產期", "目前全年可生產，但產量主要集中於10月至翌年3月", "農業知識入口網（農產品產期產地）", "https://kmweb.coa.gov.tw/theme_data.php?theme=production_map&id=103", "official", "2026-08-19"),
    ("yangtao", "採收方式", "果實採收後糖分不再增加但果皮顏色仍會轉變，通常在轉色初期至50%轉色時採收，可延長貯架壽命", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=11629", "official", "2026-08-19"),

    # 釋迦 - 農業知識入口網 釋迦主題館 subject id=15111
    ("shijia", "適合溫度", "生育溫度15～32℃間最佳", "農業知識入口網（釋迦主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=15111", "official", "2026-08-19"),
    ("shijia", "土壤條件", "排水良好之砂質壤土最適合", "農業知識入口網（釋迦主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=15111", "official", "2026-08-19"),
    ("shijia", "定植適期", "翌年1～2月間，於苗木落葉後新芽萌發前定植於園間；定植後注意澆水，避免再移植", "農業知識入口網（釋迦主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=15111", "official", "2026-08-19"),
    ("shijia", "栽植行株距", "軟枝品系與台東1號：5×4.5公尺；粗鱗品系：5×4公尺；紫色品系與台東2號：4.5×3.5公尺", "農業知識入口網（釋迦主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=15111", "official", "2026-08-19"),
    ("shijia", "開花結果習性", "冬季修剪後4、5月開花，6～7月盛花，8月底結束；夏季修剪(7、8月)後7～10天萌芽開花，9月底或10月初結束", "農業知識入口網（釋迦主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=15111", "official", "2026-08-19"),
    ("shijia", "全國產期", "第1次產期7～11月，第2次產期12～2月；8～9月、12～1月為盛產期，4～6月為無果期", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2110", "official", "2026-08-19"),

    # 甜柿 - 農業知識入口網 甜柿主題館 subject id=29734
    ("tianshi", "適合溫度", "年平均溫13℃以上；生長期(4～10月)均溫17℃以上；果實發育至成熟期(8～11月)均溫18～19℃；根系生長最適溫21～24℃", "農業知識入口網（甜柿主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29734", "official", "2026-08-19"),
    ("tianshi", "適栽海拔", "台中以北需海拔600～1,000公尺；南投及嘉義需海拔900～1,300公尺；溫量指數100～120，日均溫≥10℃日數215～240天", "農業知識入口網（甜柿主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29734", "official", "2026-08-19"),
    ("tianshi", "休眠條件", "需累積7.2℃以下低溫800～1,000小時才能進入休眠；積溫達550℃才能打破休眠發芽", "農業知識入口網（甜柿主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=29734", "official", "2026-08-19"),
    ("tianshi", "落果防治", "環刻為普遍使用之落果防治法，操作時期約在清明前後", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10252", "official", "2026-08-19"),

    # 洋香瓜 - 農業知識入口網（農產品產期產地）theme_data production_map id=5
    ("yangxiangua", "全國產期", "5月至12月", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=5", "official", "2026-08-19"),
    ("yangxiangua", "選購方式", "蒂頭及臍部較開展；輕搖有聲音者品質較不佳；外觀紋路明顯開展且分佈均勻；選硬度高者", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=5", "official", "2026-08-19"),

    # 龍鬚菜 - 農業知識入口網（農產品產期產地）theme_data production_map id=40 + 使用者問答補充
    ("longxucai", "全國產期", "4月至10月", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=40", "official", "2026-08-19"),
    ("longxucai", "適合溫度", "生育適溫18～28℃，12℃以下停止生長，超過30℃生長勢較弱", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2373", "qa", "2026-08-19"),
    ("longxucai", "土壤條件", "適應性較廣，pH5.5～7.5皆可，以含多量腐植質、保水力強的壤土或黏質壤土較理想", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2373", "qa", "2026-08-19"),
    ("longxucai", "繁殖方式", "大多以果實直接育芽種植；未發芽果實可催芽，置紙箱暗處7～14天", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2373", "qa", "2026-08-19"),
    ("longxucai", "採收方式", "夏季每3天、冬季每10天採收一次，取嫩梢約15～20公分部份", "農業知識入口網（使用者問答/種植教學）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2373", "qa", "2026-08-19"),

    # 山蘇 - 農業知識入口網 原住民族農產業主題館 subject id=39518
    ("shansu", "適合季節", "一年四季皆可採食，夏季高溫期生長快速，冬季低溫期生長緩慢", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39518", "official", "2026-08-19"),
    ("shansu", "種植方式", "可用盆栽或附植於蛇木板栽種，原生長在海拔2,500公尺以下山區潮濕的樹幹、石頭上或腐植土堆積地面", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39518", "official", "2026-08-19"),
    ("shansu", "環境條件", "耐旱但忌強光，需遮光下才能生長良好，喜陰濕環境", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39518", "official", "2026-08-19"),
    ("shansu", "產地分布", "廣泛分布於台灣中低海拔(500～2,500公尺)山區，人工栽培以花蓮縣及屏東縣最多", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39518", "official", "2026-08-19"),

    # 過貓（過溝菜蕨）- 農業知識入口網 原住民族農產業主題館 subject id=39527
    ("guomao", "適合季節", "一年四季均可種植，以春季最適宜", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39527", "official", "2026-08-19"),
    ("guomao", "適合溫度", "氣溫25～32℃左右，雨林氣候生長良好", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39527", "official", "2026-08-19"),
    ("guomao", "種植方式", "以紗網遮蔭種植，葉片生長更嫩、品質更佳", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39527", "official", "2026-08-19"),
    ("guomao", "產期", "產期集中夏季，雨水越多生長越佳，5～10月為盛產期，8～9月產量最多", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39527", "official", "2026-08-19"),
    ("guomao", "採收時機", "嫩芽尚未展開或稍展開而葉柄尚易折取時，莖葉最細嫩", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39527", "official", "2026-08-19"),

    # 甜菜根 - 農業知識入口網 knowledge_view id=2331
    ("tiancaigen", "適合季節", "平地10～11月，高冷地3～4月為播種適期", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2331", "official", "2026-08-19"),
    ("tiancaigen", "適合溫度", "生育適溫15～20℃，性喜冷涼不耐暑熱", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2331", "official", "2026-08-19"),
    ("tiancaigen", "土壤條件", "肥沃適潤之壤土或砂質壤土為佳，排水及日照需良好", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2331", "official", "2026-08-19"),
    ("tiancaigen", "水分管理", "生育期水分補給要充足，忌乾旱缺水", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2331", "official", "2026-08-19"),
    ("tiancaigen", "生長期", "60～80天；秋冬台灣雲嘉地區為主要產區", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2331", "official", "2026-08-19"),

    # 荸薺（馬蹄）- 農業知識入口網 knowledge_view id=2371
    ("biqi", "適合季節", "春末將種球淺植於土中，經7天後灌水淹滿，再經月餘長出葉狀莖", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2371", "official", "2026-08-19"),
    ("biqi", "適合溫度", "生育適溫30～35℃，球莖肥大期宜降至22～26℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2371", "official", "2026-08-19"),
    ("biqi", "種植方式", "繁殖用分蘗莖或球莖栽植，種植深度約4公分，需水深2～5公分的水田", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2371", "official", "2026-08-19"),
    ("biqi", "土壤條件", "培養土以砂質壤土或腐植質壤土為佳，栽培土質以潮濕之壤土為佳", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2371", "official", "2026-08-19"),
    ("biqi", "水分管理", "生育期間不可斷水，至採收前才乾燥土壤", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2371", "official", "2026-08-19"),
    ("biqi", "生長週期與產期", "從栽培到收穫約120天；盛產期11月至翌年3月，早熟種產期11～12月，晚熟種產期12月至翌年3月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2371", "official", "2026-08-19"),

    # 蘋果 - 農業知識入口網
    ("pingguo", "適合環境", "年平均溫9～14℃、冬季7.2℃以下低溫累積達1,400小時以上才適合，台灣僅高冷地（梨山、福壽山、武陵農場等）可栽培", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=85", "official", "2026-08-19"),
    ("pingguo", "開花結果期", "農曆12月至翌年1月開花，4、5月結果；高冷地盛產期8～11月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=5254", "official", "2026-08-19"),
    ("pingguo", "平地栽培（熱帶品種）", "熱帶蘋果耐平地氣候但不耐過濕，需異株授粉需買兩株；需人工於農曆11月底強迫落葉促進開花；官方明確表示尚不建議經濟栽培，果實會偏小", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6926", "official", "2026-08-19"),

    # 枇杷 - 農業知識入口網
    ("pipa", "生育週期", "一年培苗、二年移栽、三年嫁接、四年定植，十年後進入旺盛期", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10475", "qa", "2026-08-19"),
    ("pipa", "栽植地點", "選擇地勢高爽、土層深厚、便於排水積肥之處", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10475", "qa", "2026-08-19"),
    ("pipa", "施肥", "第1次施肥8～9月開花前；第2次11～12月花瓣脫落後至翌年1月；第3次約4月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10475", "qa", "2026-08-19"),
    ("pipa", "採收（依熟期）", "早熟種5月下旬，中熟種6月上旬，遲熟種6月上中旬", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10475", "qa", "2026-08-19"),

    # 紅棗 - 農業知識入口網 紅棗主題館
    ("hongzao", "生育特性", "幼年期較其他果樹短，前3年整枝配置枝條位置以培養樹型及結果母枝，第4年開始結果採收", "農業知識入口網（紅棗主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39152", "qa", "2026-08-19"),
    ("hongzao", "萌芽開花", "3月萌芽開花，授粉後進入果實生長期；枝條有刺狀托葉需人工摘除避免傷果", "農業知識入口網（紅棗主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39152", "qa", "2026-08-19"),
    ("hongzao", "採收", "產期約1個月，7月中旬果皮由綠轉紅開始採收，7～8月為採收期", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7555", "qa", "2026-08-19"),

    # 酪梨 - 農業知識入口網 酪梨(幸福果)主題館 subject id=25561/25565
    ("laoli", "定植適期", "春季3～4月和秋季11月為栽植適期；蔭棚或溫室培養苗木定植前宜移至戶外健化2、3週", "農業知識入口網（酪梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=25561", "official", "2026-08-19"),
    ("laoli", "種植密度", "行距及株距約5～6公尺，每公頃約可植277～400株；初期可間植蔬菜、木瓜等增加收益", "農業知識入口網（酪梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=25561", "official", "2026-08-19"),
    ("laoli", "品種配置", "須種植不同開花習性的品種配合才可結果，選擇適宜授粉品種對產量很重要", "農業知識入口網（酪梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=25561", "official", "2026-08-19"),
    ("laoli", "各品種產期", "嘉選一號(嘉義)8～9月；嘉選二號(麻豆)8～9月；嘉選三號(嘉義)8～10月初；嘉選四號(嘉義台南)6月中～7月中，為最早生品種；Choquette最晚12月上旬", "農業知識入口網（酪梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=25565", "official", "2026-08-19"),

    # 大豆（黃豆）- 農業知識入口網 knowledge_view id=1576
    ("dadou", "適合季節", "5月播種（不遲於6月），10月收耕；生長季約4個月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1576", "official", "2026-08-19"),
    ("dadou", "適合溫度", "發芽最低溫6～18℃，以10～12℃發芽正常；生育期間15～25℃最適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1576", "official", "2026-08-19"),
    ("dadou", "水分需求", "5、6月發芽期雨量正常至稍高為宜；7、8月開花結莢期濕度要求較高", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1576", "official", "2026-08-19"),
    ("dadou", "採收判斷", "葉片及葉柄枯黃脫落，莢果由綠轉黃後乾燥呈褐色或黃褐色，手輕打莢果有響聲即為採收適期", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1576", "official", "2026-08-19"),

    # 金針 - 農業知識入口網 金針主題館 subject id=24164
    ("jinzhen", "適合環境（本地種／高山種）", "必須於北部海拔400公尺、東部海拔600～800公尺以上山區才能穩定抽苔開花", "農業知識入口網（金針主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24164", "official", "2026-08-19"),
    ("jinzhen", "適合環境（平地種／台東6號）", "全台各地均能栽培開花，但冬季葉片會乾枯休眠", "農業知識入口網（金針主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24164", "official", "2026-08-19"),
    ("jinzhen", "土壤條件", "富含有機質之砂質壤土為佳，pH5.5～6.5，耐旱性強但忌潮濕積水", "農業知識入口網（金針主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24164", "official", "2026-08-19"),
    ("jinzhen", "種植方式", "分株繁殖除冬季低溫期外全年皆可進行；種子繁殖以春秋兩季播種成活率較高", "農業知識入口網（金針主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24164", "official", "2026-08-19"),
    ("jinzhen", "產期", "本地種產季為秋季7月下旬至9月中旬；台東6號產季為夏季5月上旬至6月中旬；台東7號花期4～7月可二次開花", "農業知識入口網（金針主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24295", "official", "2026-08-19"),

    # 仙草 - 農業知識入口網 藥用植物主題館 subject id=37485
    ("xiancao", "適合溫度", "適宜生長氣溫約20～25℃", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37485", "official", "2026-08-19"),
    ("xiancao", "土壤條件", "排水良好之砂質壤土最適宜", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37485", "official", "2026-08-19"),
    ("xiancao", "育苗與繁殖", "利用扦插法繁殖，8月於本田選健壯莖插植於苗圃，翌年2～3月重新萌發新枝時挖取種苗移植本田", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37485", "official", "2026-08-19"),
    ("xiancao", "選地整地", "忌連作，種植地宜選有機水稻後作地，或經半年以上休閒並曾浸水6個月以上的土壤", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37485", "official", "2026-08-19"),
    ("xiancao", "施肥", "有機質肥料每公頃8,000～10,000公斤，種植前2週施用於田間", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37485", "official", "2026-08-19"),
    ("xiancao", "採收與花期", "頂芽與腋芽長出花蕾時為採收期，花期10～12月", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37485", "official", "2026-08-19"),

    # 洛神葵 - 農業知識入口網 洛神葵主題館 subject id=26447
    ("luoshenkui", "適合季節", "播種期4～6月，生長期約4個月", "農業知識入口網（洛神葵主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=26447", "official", "2026-08-19"),
    ("luoshenkui", "土壤與地點", "宜於低海拔排水良好地區栽培，避免根系泡水腐爛，以低海拔緩坡山坡地栽培最理想", "農業知識入口網（洛神葵主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=26447", "official", "2026-08-19"),
    ("luoshenkui", "種植方式", "選雨後晴天播種，行株距2公尺×1.5公尺", "農業知識入口網（洛神葵主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=26447", "official", "2026-08-19"),
    ("luoshenkui", "施肥", "混合有機質肥料，每公頃施用1公噸時鮮果萼產量可達5.4公噸", "農業知識入口網（洛神葵主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=26447", "official", "2026-08-19"),
    ("luoshenkui", "產期（依熟期）", "早生種8～9月，中生種10～11月，晚生種12月至翌年1月，盛產期8～10月", "農業知識入口網（洛神葵主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=26447", "official", "2026-08-19"),

    # 咖啡 - 農業知識入口網 咖啡主題館 subject id=45553
    ("kafei", "播種與定植適期", "種子可秋季10～12月及春季2～4月間播種，發芽率50～80%；植株定植時間以12～3月最適合，雨季前種植有助樹苗存活", "農業知識入口網（咖啡主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=45553", "official", "2026-08-19"),
    ("kafei", "發芽時間", "新鮮種子播種後5～8星期發芽", "農業知識入口網（咖啡主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=45553", "official", "2026-08-19"),
    ("kafei", "株距（依品種）", "阿拉比卡2.5×2.5公尺(約1,600株/公頃)；羅布斯塔3.0×3.0公尺(約1,100株/公頃)；賴比瑞亞3.5×3.5公尺(約800株/公頃)", "農業知識入口網（咖啡主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=45553", "official", "2026-08-19"),
    ("kafei", "適合溫度與環境", "適應16～28℃之間溫度，栽培環境需涼爽通風、有樹蔭或防風樹，年降雨量1500～2500毫米較適宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6018", "qa", "2026-08-19"),
    ("kafei", "花期與採收", "每年國曆2、3月為花期，開花後結綠色果實，農曆中秋過後由綠轉紅開始收成；低海拔採收期10月至12月中旬，高海拔可延至翌年3、4月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6018", "qa", "2026-08-19"),

    # 菱角 - 農業知識入口網（農產品產期產地）
    ("lingjiao", "全國產期", "產期8月開始，9～11月為盛產期，每2週採收一次共6～7輪", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=113", "official", "2026-08-19"),
    ("lingjiao", "主要產區", "台南官田為全國最大產區，栽培面積約353公頃，年產量約4,000公噸，占全國約90%", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=113", "official", "2026-08-19"),

    # 野蓮 - 使用者問答/種植教學整理
    ("yelian", "種植方式", "須於魚塭或池塘中栽培，進水口需加裝濾網過濾雜物並防治福壽螺；莖長可達130公分以上，由節處長出不定根繁殖", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=news&sub_theme=agri_life&id=52453", "qa", "2026-08-19"),
    ("yelian", "生長週期", "夏季生長較快約2個月可採收，冬季生長較慢約3個月，換季種植之間會曬池數天，一年可採收3～4次", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=news&sub_theme=agri_life&id=52453", "qa", "2026-08-19"),
    ("yelian", "採收方式", "先將水位降到約手臂高度，伸手觸及假莖底下根部自根部整株拔起，再經剪根、清洗、分級、秤重、包裝", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=news&sub_theme=agri_life&id=52453", "qa", "2026-08-19"),

    # 樹豆 - 農業知識入口網 藥用植物主題館 subject id=37351
    ("shudou", "生育特性", "耐貧瘠、乾旱，不耐寒忌霜害；根系淺易受風害，應選避風地區種植", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37351", "official", "2026-08-19"),
    ("shudou", "開花結莢特性", "花序屬無限型生長，開花、結莢及豆莢成熟時間參差不一，採收無法一致；花果期春、夏間", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37351", "official", "2026-08-19"),
    ("shudou", "分布地區", "台灣各地零星栽培，大多於海拔1,000公尺以下淺山坡地、丘陵地及河床地", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37351", "official", "2026-08-19"),

    # 台灣藜 - 農業知識入口網 原住民族農產業主題館 subject id=39491
    ("taiwanli", "生育特性", "植株生長強健，耐旱性及耐瘠性極佳，生長期短，播種後90～100天即可成熟（依季節及品系而異）", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39491", "official", "2026-08-19"),
    ("taiwanli", "栽培背景", "台灣原生種植物，原住民部落耕種百年以上歷史，常作為小米、玉米伴生作物；籽實富含天然色素", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39491", "official", "2026-08-19"),

    # 小米 - 農業知識入口網 小米及台灣藜主題館 subject id=32193/32233
    ("xiaomi", "適合季節", "台灣以春、秋兩作皆可種植，但春作產量較秋作佳", "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32193", "official", "2026-08-19"),
    ("xiaomi", "適合溫度", "發芽最低溫7℃，以18～24℃發芽最快，可在-2℃至-3℃之早霜下生長", "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32193", "official", "2026-08-19"),
    ("xiaomi", "土壤條件", "有機質含量豐富、排水良好、微酸性或中性(pH4.9～6.2)之壤土或砂質壤土", "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32233", "official", "2026-08-19"),
    ("xiaomi", "生育期與水分", "生育期3.5～4個月，一年可兩作；臨界需水期為拔節至開花期、及籽實形成期", "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32231", "official", "2026-08-19"),

    # 檸檬 - 農業知識入口網
    ("ningmeng", "全國產期", "經產期調節全年均可生產，盛產期6～8月；主要開花期12～2月，10～12月亦為盛產期", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=152", "official", "2026-08-19"),
    ("ningmeng", "土壤與品種", "台灣主要品種優利卡(Eureka)容易周年開花結果，俗稱四季檸檬；土壤以排水砂質壤土較合適，pH5.5～7.0為宜", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3348", "qa", "2026-08-19"),
    ("ningmeng", "採收標準", "果實長到直徑約5.5～6公分，或果汁率35%以上即可採收", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3348", "qa", "2026-08-19"),

    # 紅蔥頭 - 種植教學整理，qa等級
    ("hongcongtou", "適合季節", "最佳種植季節為秋季，但台灣幾乎全年可種植", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=16506", "qa", "2026-08-19"),
    ("hongcongtou", "適合溫度", "發芽適溫15～30℃，以20℃最適合", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=16506", "qa", "2026-08-19"),
    ("hongcongtou", "土壤條件", "黏質壤土較適合，pH5.7～7.4", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=16506", "qa", "2026-08-19"),
    ("hongcongtou", "種球休眠與採收", "種球需日照6週以上休眠期才能再種；第一次採收葉莖約需1個月", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=16506", "qa", "2026-08-19"),

    # 辣椒 - 農業知識入口網 knowledge_view id=14506
    ("lajiao", "適合季節", "全年皆可栽種，考量本土季風氣候以春作及初秋較合適", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=14506", "official", "2026-08-19"),
    ("lajiao", "適合溫度", "種子發芽適溫25～30℃，生長溫度範圍15～30℃，最適溫度約25℃", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=14506", "official", "2026-08-19"),
    ("lajiao", "土壤條件", "pH5.5～6.8皆適宜，根系發達適合土層深厚、排水優良的砂質壤土", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=14506", "official", "2026-08-19"),
    ("lajiao", "水分管理", "不耐濕不耐旱，需定期澆水但不能積水，水分管理很重要", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=14506", "official", "2026-08-19"),
    ("lajiao", "採收", "果實充分肥大時為最佳採收期，採收期約可達3個月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=14506", "official", "2026-08-19"),

    # 青江菜 - 農業知識入口網 knowledge_view id=2374
    ("qingjiangcai", "適合季節", "除嚴冬外整年皆可栽培；春秋季播種45～50天、夏季35～40天可收成", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2374", "official", "2026-08-19"),
    ("qingjiangcai", "播種方式", "直播後疏苗或苗盆培育後移植；行距10～15公分、株距5公分，每洞點播4～5粒種子", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2374", "official", "2026-08-19"),
    ("qingjiangcai", "疏苗步驟", "一週後疏苗每洞留3株；兩週後本葉3～4片時留2株；三週後株根膨脹時只留1株", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2374", "official", "2026-08-19"),
    ("qingjiangcai", "水肥管理", "不耐乾燥需勤澆水，生長快速需不斷施肥，肥料撒在行間", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2374", "official", "2026-08-19"),
    ("qingjiangcai", "採收時機", "長到約15公分、近株根處變結實時即可收成", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2374", "official", "2026-08-19"),

    # 芹菜 - 農業知識入口網
    ("qincai", "適合季節", "全年生產之葉菜類，盛產期春、秋、冬季，夏季需中高海拔或降溫設施才容易生長", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=155", "qa", "2026-08-19"),
    ("qincai", "品種", "台灣常栽培黃梗菜、青梗菜、芹菜管三種，其中黃梗種葉梗黃白色粗長，可食性最高", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=155", "qa", "2026-08-19"),

    # 扁蒲（蒲瓜）- 農業知識入口網 扁蒲主題館 subject id=24666
    ("bianbu", "適合溫度", "種子發芽適溫25～30℃，生長發育適溫25～28℃，結果適溫20～25℃；持續高溫35℃或低溫15℃左右發育會受阻", "農業知識入口網（扁蒲主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24666", "official", "2026-08-19"),
    ("bianbu", "整枝摘心", "母蔓長至6～7葉片時摘心，留健壯子蔓3～4條，子蔓長至5～6葉時再進行第二次摘心", "農業知識入口網（扁蒲主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24666", "official", "2026-08-19"),
    ("bianbu", "採收時機", "食用幼嫩果實，夏天雌花開花後6～8天為採收適期，秋冬季則8～10天", "農業知識入口網（扁蒲主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24666", "official", "2026-08-19"),

    # 胡瓜（花胡瓜）- 農業知識入口網
    ("hugua", "產期（高屏地區）", "周年可以生產，往年以秋冬裡作為主要產期，盛產季節集中冬、春兩季", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=158", "official", "2026-08-19"),
    ("hugua", "栽培方式", "分露天栽培、網室栽培及設施栽培；設施栽培屋頂覆蓋透明塑膠布可阻擋雨水傳播病害（如露菌病、炭疽病），四周防蟲網防止害蟲進入", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=12925&id=316535", "official", "2026-08-19"),
    ("hugua", "採收技術", "播種後40～45天開花，開花後5～7天、果實長16～18公分時採收，宜清晨或傍晚採收，每日可採，每0.1公頃產量可達2,500～3,000公斤", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=12925&id=316535", "official", "2026-08-19"),

    # 薑黃 - 農業知識入口網 藥用植物主題館 subject id=37486
    ("jianghuang", "適合季節", "種植適期一般3～5月，以4月份種植最佳", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37486", "official", "2026-08-19"),
    ("jianghuang", "土壤條件", "土層深厚、土質疏鬆肥沃及排水良好的砂質壤土；喜氣候濕潤、陽光充足、雨量充足", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37486", "official", "2026-08-19"),
    ("jianghuang", "繁殖與種植", "以根莖繁殖，選直徑約2.5～3公分、無病蟲害完整的根莖作種苗；行株距90×30公分，覆土深度10～15公分", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37486", "official", "2026-08-19"),
    ("jianghuang", "施肥", "有機質肥料每公頃6,000～8,000公斤，種植前2週施用於田間", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37486", "official", "2026-08-19"),
    ("jianghuang", "採收", "種植後約8～10個月可收穫，收穫期12月至翌年2月；植株莖葉逐漸枯萎、塊根充實時即可採收", "農業知識入口網（藥用植物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=37486", "official", "2026-08-19"),

    # 藍莓 - 農業知識入口網
    ("lanmei", "土壤與環境", "喜全日照，土壤及介質需有機質含量高、疏鬆、適量酸度，pH值需低於5.2", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=420759", "qa", "2026-08-19"),
    ("lanmei", "授粉", "花期需授粉昆蟲，兔眼藍莓需混植2品種以上有利結實", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=420759", "qa", "2026-08-19"),
    ("lanmei", "花芽分化", "夏季培養健壯枝條有利秋冬季花芽分化", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=420759", "qa", "2026-08-19"),
    ("lanmei", "產期", "台灣11月起零星開花，3～4月盛花，4～5月中果實開始成熟，產期至7月底結束；開花至採收約60～90天", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=416564", "qa", "2026-08-19"),

    # 皇帝豆（萊豆）- 農業知識入口網
    ("huangdidou", "適合溫度", "生長適溫約15～25℃，短日照植物，長日照下開花結果會延遲", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4739", "official", "2026-08-19"),
    ("huangdidou", "土壤條件", "喜排水良好，pH6～7的砂質壤土，根部忌淹水，採作畦栽培為主", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4739", "official", "2026-08-19"),
    ("huangdidou", "種植注意", "若提早於7～8月種植，幼苗根部可能因塑膠布日照高溫受損，定植後可於周圍覆蓋稻草降低日曬影響", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4739", "official", "2026-08-19"),
    ("huangdidou", "採收", "由11月開始採收至隔年5月，採收期長達6～7個月；採收期間需去除部分老葉老藤以增加通風、降低病蟲害", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4739", "official", "2026-08-19"),

    # 球莖甘藍（結頭菜）
    ("qiujingganlan", "植物特性", "十字花科蕓苔屬一年生草本植物，喜冷涼氣候，需日照充足，耐寒耐霜，以種子繁殖", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=175", "official", "2026-08-19"),
    ("qiujingganlan", "採收天數", "播種育苗移植後，早生種約55～60天可採收，晚生種約80～100天可採收", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=175", "official", "2026-08-19"),

    # 越瓜（醃瓜）
    ("yuegua", "適合季節", "性喜高溫多濕，台灣一般在春季至夏季栽種", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=145", "qa", "2026-08-19"),

    # 豇豆（長豆）
    ("jiangdou", "植物特性", "豆科豇豆屬一年生蔓性或矮性草本植物，性喜日照充足氣候，耐熱性強、耐寒性弱；台灣一般栽培蔓性長豇豆，需立支架，生長期較長、產量較高", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=169", "official", "2026-08-19"),
    ("jiangdou", "採收方式", "成熟時果莢發育快速，開始採收後幾乎每隔1～2天便要採收一次", "農業知識入口網（農產品產期產地）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=169", "official", "2026-08-19"),

    # 米豆
    ("midou", "植物特性", "豆科豇豆屬一年生草本作物，生長適溫25～35℃，大多具短日開花特性，含必需胺基酸，鈣質與鐵質高於一般豆類，東南亞地區常與玉米間作", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39498", "official", "2026-08-19"),

    # 甘蔗 - 農業知識入口網 knowledge_view id=2377
    ("ganzhe", "適合季節", "春植期1～3月，秋植期7～8月，補植期1～5月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2377", "official", "2026-08-19"),
    ("ganzhe", "生長期", "一般為18個月；收成尖峰期曾為12月至翌年4月", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2377", "official", "2026-08-19"),
    ("ganzhe", "栽培環境", "適合栽種於土壤肥沃、陽光充足、冬夏溫差大的地方", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2377", "official", "2026-08-19"),

    # 胡麻（芝麻）- 農業知識入口網 胡麻主題館 subject id=40446
    ("huma", "適合季節", "春、秋兩栽培期作，台灣以秋作栽培面積較大、產量較多；春作採收6～7月，秋作採收11月中至12月", "農業知識入口網（胡麻主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40446", "official", "2026-08-19"),
    ("huma", "生育期", "秋作生育期約80～90天，屬中熟品種", "農業知識入口網（胡麻主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40446", "official", "2026-08-19"),
    ("huma", "主要品種", "台南1號，黑色種皮，秋作平均產量每公頃約1,068公斤，油脂含量52～56%，具強桿抗倒伏特性", "農業知識入口網（胡麻主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40446", "official", "2026-08-19"),

    # 杭菊 - 農業知識入口網 機能作物主題館 subject id=40308/40309
    ("hangju", "適合季節與溫度", "一般於4月清明節後開始種植，最晚可於7月前；生長適溫15～28℃", "農業知識入口網（機能作物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40308", "qa", "2026-08-19"),
    ("hangju", "土壤條件", "排水良好、pH5.2～6.7的砂質壤土為佳；耐旱不耐淹水", "農業知識入口網（機能作物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40308", "official", "2026-08-19"),
    ("hangju", "作畦與定植", "畦高30公分以上（減少萎凋病發生），畦寬約105～110公分、畦溝寬約45公分；採雙行三角種植，行株距約60×60公分，以分株苗為主", "農業知識入口網（機能作物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40309", "official", "2026-08-19"),
    ("hangju", "花期與採收", "花期11～12月，於花序舌狀花展開7～8分時採摘，可分3～4次採收", "農業知識入口網（機能作物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40309", "official", "2026-08-19"),
]

PESTS = [
    # 小白菜
    ("xiaobaicai", "斑潛蠅（畫圖蟲）", "蟲害", "在葉片穿刺產卵，幼蟲孵化後潛食葉肉，呈白色不規則線條",
     "摘除被害葉並清出田外；栽植前後淹水48小時；黃色黏板誘捕；生物天敵（釉小蜂）",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6139", "official", "2026-08-19"),
    ("xiaobaicai", "小菜蛾", "蟲害", "幼蟲取食葉片，十字花科蔬菜常見害蟲",
     "苦楝油100～500倍（可調1000倍）小量測試，勿加展著劑以避免藥害；蘇力菌亦有效",
     "桃園區農改場問答", "https://kmweb.moa.gov.tw/subject/subject.php?id=7654", "qa", "2026-08-19"),
    ("xiaobaicai", "黃條葉蚤", "蟲害", "生活習性使其難以防治，十字花科蔬菜常見害蟲",
     "菸葉水500～1000倍小量測試，須單獨使用，注意藥害與尼古丁毒性防護",
     "桃園區農改場問答", "https://kmweb.moa.gov.tw/subject/subject.php?id=7654", "qa", "2026-08-19"),

    # 地瓜葉（同株植物，資料來自甘藷病蟲害管理正式頁，非葉片專屬但適用）
    ("digualve", "甘藷蟻象", "蟲害", "危害塊根，為甘藷最常見害蟲",
     "每公頃施用2.5%陶斯松粉劑45公斤於莖蔓間，間隔7～10天施用一次，連續3～4次；另可設置性費洛蒙誘蟲盒",
     "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=19321", "official", "2026-08-19"),
    ("digualve", "甘藷猿葉蟲", "蟲害", "成蟲啃食嫩葉及莖，幼蟲潛入土中啃食塊根表皮形成凹道",
     "每公頃施用2.5%陶斯松粉劑45公斤，間隔7～10天施用一次，連續3～4次",
     "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=19321", "official", "2026-08-19"),
    ("digualve", "甘藷簇葉病", "病害", "葉片變小扭曲、節間縮短、腋芽叢生、植株矮化呈簇生狀",
     "選擇健康種苗、加強田間衛生、防除媒介昆蟲",
     "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=19321", "official", "2026-08-19"),

    # 空心菜
    ("kongxincai", "葉蟎（紅蜘蛛）", "蟲害", "刺吸式口器吸食汁液，破壞葉綠素，葉表出現白色斑點，密度高時導致落葉",
     "噴灌設備定期噴水降低密度；修剪植株使通風日照良好；避免過量施氮肥；噴施窄域油/葵無露等乳化油劑300～500倍；可濕性硫磺粉稀釋500倍噴施",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=12935", "official", "2026-08-19"),

    # 蘿蔔
    ("luobo", "小菜蛾／黃條葉蚤", "蟲害", "十字花科常見害蟲，取食葉片造成孔洞",
     "與非十字花科作物輪作；防治方式可參考小白菜同類害蟲防治法（苦楝油、菸葉水）",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3942", "qa", "2026-08-19"),
    ("luobo", "紋白蝶", "蟲害", "喜於葉片產卵，大量幼蟲啃食葉片僅剩葉梗",
     "覆蓋防蟲網並定期檢查漏洞；種植前土地薰蒸消毒清除潛伏蟲卵；人工捕捉（不噴藥時的替代方案）",
     "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3942", "qa", "2026-08-19"),

    # 高麗菜
    ("gaolicai", "甘藍黑腐病", "病害", "葉片邊沿乾萎，並出現黃化徵狀（細菌性病害）",
     "10%維利黴素溶液600倍或81.3%嘉賜銅可濕性粉劑1000倍噴施；保持田間清潔並及時清除病蟲害源",
     "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/subject/subject.php?id=59338", "qa", "2026-08-19"),

    # 大白菜
    ("dabaicai", "根蛆（種蠅幼蟲）", "蟲害", "幼蟲危害根部，是大白菜常見蟲害",
     "根際施用草木灰，或草木灰、石灰與敵百蟲粉混合撒施於菜根周圍；發現根蛆時可用敵百蟲液灌根",
     "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2869", "qa", "2026-08-19"),
    ("dabaicai", "霜霉病", "病害", "蓮座期常見病害",
     "9月中旬至10月中旬每7～10天噴藥一次、連續3～4次，使用40%乙磷鋁或瑞毒霉混合液；發病植株需及時拔除並對周圍土壤消毒",
     "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2869", "qa", "2026-08-19"),

    # 花椰菜
    ("huaqielan", "黑斑病", "病害", "學名Alternaria brassicicola，葉片出現2～10公分同心輪紋狀圓形褐色病斑，老葉較易發生，嚴重時可致幼苗猝倒；種子受害會降低發芽率",
     "10%保粒黴素可濕性粉劑1000倍稀釋噴灑；種子以50℃溫水浸泡30分鐘消毒；發現初期及早拔除燒毀病株；避免連作並與非寄主作物輪作",
     "農業知識入口網（花椰菜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30128", "official", "2026-08-19"),

    # 小黃瓜
    ("xiaohuanggua", "白粉病", "病害", "好發於秋冬及春季，適合發病環境為乾燥涼冷、日照不足",
     "小蘇打粉稀釋1000倍於好發季節前2～3天噴1次；棕櫚灰或草木灰稀釋500～1000倍每4～5天噴1次；亞磷酸稀釋500～1000倍混合窄域油稀釋500倍每6～7天噴1次（亞磷酸為強酸不可直接與氫氧化鉀混合，建議先小規模試用2～3天）",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8696", "official", "2026-08-19"),

    # 茄子 - 農業知識入口網 茄子主題館 subject id=19075（節選最常見的4項，其餘6病7蟲害見原文）
    ("qiezi", "青枯病", "病害", "白天高溫時部分葉片萎凋，夜晚或雨後恢復，最終全株呈綠色枯萎；維管束褐變並溢出白濁色粘液",
     "避免多灌水；避免連作；使用健康苗；土壤處理；與水稻輪作",
     "農業知識入口網（茄子主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19075", "official", "2026-08-19"),
    ("qiezi", "白粉病", "病害", "葉片上表面形成白黴狀圓形斑點，導致植株生長勢衰弱",
     "避免密植保持通風；摘除病株焚毀；施用平克座、菲克利、邁克尼、賽福座等推薦藥劑，採收前3天停止施藥",
     "農業知識入口網（茄子主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19075", "official", "2026-08-19"),
    ("qiezi", "二點小綠葉蟬", "蟲害", "被害嫩芽捲縮不展；葉片先由邊緣呈淡黃色，逐漸向下皺縮枯萎",
     "種植豆科植物做保護；施用25%丁基加保扶可濕性粉劑700倍或85%加保扶可濕性粉劑2000倍，採收前9天停止施藥",
     "農業知識入口網（茄子主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19075", "official", "2026-08-19"),
    ("qiezi", "紅蜘蛛類", "蟲害", "造成葉片黃化甚至落葉，影響光合作用使植株生長勢減弱",
     "施用2%密滅汀1500倍防治，採收前14天停止用藥",
     "農業知識入口網（茄子主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19075", "official", "2026-08-19"),

    # 甜椒
    ("tianjiao", "果腐病", "病害", "由甜椒果腐病菌(Phomopsis capsici)引起，主要發生期9～11月",
     "23.6%百克敏乳劑或50%貝芬替水懸劑防治（半致效濃度0.5～1及0.1～0.5 ppm），搭配移除病原、避免果實傷口",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=1&type=13143&id=168641", "official", "2026-08-19"),
    ("tianjiao", "炭疽病", "病害", "台灣有4種炭疽病菌可感染甜椒(主要為Colletotrichum gloeosporioides)，主要發生期6～11月",
     "23.6%百克敏乳劑或50%貝芬替水懸劑防治，搭配移除病原、避免果實傷口",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=1&type=13143&id=168641", "official", "2026-08-19"),

    # 洋蔥
    ("yangcong", "細菌性軟腐病", "病害", "植物組織褐變、軟化、腐爛下垂、散發臭味，嚴重時全株死亡；好發於潮濕、多雨、強風、25～30℃環境",
     "避免連作與其他作物輪作；選用健康種苗；多施有機肥及合理化施肥；病害發生後盡量移除罹病組織",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=13179&id=228008", "official", "2026-08-19"),
    ("yangcong", "紫斑病", "病害", "葉片產生紫色、褐黑色紡錘形病斑，邊緣或末端黃化；好發於18～25℃連續潮濕環境",
     "避免連作與其他作物輪作；選用健康種苗；病害發生後盡量移除罹病組織",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=2&type=13179&id=228008", "official", "2026-08-19"),

    # 絲瓜
    ("sigua", "炭疽病", "病害", "葉片最初出現黃色小斑點，漸變褐色至黑色不規則病斑，高濕時產生桔色至粉紅色分生孢子，果實腐爛",
     "清除並燒毀罹病株；加強田間衛生管理",
     "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24755", "official", "2026-08-19"),
    ("sigua", "萎凋病", "病害", "苗期生長不良、葉片不能伸展或維管束黑褐化；成株期半側褐化至蔓割病徵",
     "實施晚植以逃避苗期病害；嫁接抗病根砧於稜角絲瓜上",
     "農業知識入口網（絲瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=24755", "official", "2026-08-19"),

    # 芭樂
    ("bale", "東方果實蠅", "蟲害", "雌成蟲以產卵管在果皮內產卵，幼蟲孵化後鑽食果肉導致腐爛；幼果期受害會使果實畸形，外觀不規則凹凸",
     "釋放不孕蟲（鈷60放射線處理）；每公頃懸掛1個含毒甲基丁香油誘殺器，每7天調查一次，蟲數激增時使用藥劑防除",
     "農業知識入口網（芭樂主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=11760", "official", "2026-08-19"),

    # 茼蒿
    ("tongao", "枯葉病／炭疽病", "病害", "茼蒿常見病害之一", "噴施大仙和液防治", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "qa", "2026-08-19"),
    ("tongao", "蚜蟲／夜盜蟲／切根蟲", "蟲害", "茼蒿常見蟲害", "噴施馬拉松乳劑防治", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8363", "qa", "2026-08-19"),

    # 芥藍
    ("jielan", "黑腐病", "病害", "細菌性病害，高溫高濕環境易發生", "定期檢查葉片與莖部及早發現；使用天然農藥或肥皂水噴霧防治", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),
    ("jielan", "菜青蟲／小菜蛾／蚜蟲", "蟲害", "芥藍常見蟲害", "定期檢查葉片與莖部及早發現；使用天然農藥或肥皂水噴霧防治", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18199", "qa", "2026-08-19"),

    # 南瓜
    ("nangua", "果實蠅", "蟲害", "南瓜開花後果實易被果實蠅叮咬產卵，太晚套袋防治無效", "開花後馬上套透氣紙袋，需及時處理，太晚套袋沒有用", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6113", "qa", "2026-08-19"),
    ("nangua", "潛葉蟲", "蟲害", "以植物葉子組織為食的昆蟲幼體", "取柑橘皮浸泡後噴灑葉面防治", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3091", "qa", "2026-08-19"),

    # 苦瓜 - 農業知識入口網 苦瓜主題館 subject id=38103（病害）/ id=38105（蟲害）
    ("kugua", "白粉病", "病害", "產生白色粉末狀物（病原菌菌絲與分生胞子），漸變灰色，可感染葉片、葉柄、嫩蔓；嚴重時葉片變黃枯落，甚至全株表面覆滿白色粉狀物",
     "發病初期拔除罹病葉與枝條；噴佈葵花油＋無患子油(9:1)300倍液；未罹病前噴佈枯草桿菌製劑",
     "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38103", "official", "2026-08-19"),
    ("kugua", "病毒病", "病害", "葉片呈現綠色與淡綠色鑲崁的顏色，生長勢減弱，果實生長與外觀易受影響、產量下降；由粉蝨、蚜蟲、薊馬等傳播",
     "防治傳播媒介害蟲（粉蝨、蚜蟲、薊馬）",
     "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38103", "official", "2026-08-19"),
    ("kugua", "蔓枯病", "病害", "被害部初呈淡黃綠色油浸狀，莖基部造成潰瘍腐爛病徵",
     "與水稻輪作或種植抗病根砧之嫁接苗（萎凋病同法）",
     "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38103", "official", "2026-08-19"),
    ("kugua", "蚜蟲", "蟲害", "定植後1～2週於本葉葉背可見蚜蟲由數隻變群落，為害新芽使枝條無法正常生長，嚴重時全株枯死",
     "黃色粘紙誘殺；噴施窄域油500倍防治；釋放捕食性天敵（小黑花椿象、草蛉）",
     "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38105", "official", "2026-08-19"),
    ("kugua", "瓜實蠅", "蟲害", "苦瓜授粉後2～3天開始易被瓜實蠅產卵",
     "黃色粘紙誘殺；噴施蛋白質水解物可誘殺雌蠅及雄蠅；懸掛克蠅香誘殺器於田間",
     "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38105", "official", "2026-08-19"),
    ("kugua", "斜紋夜盜蟲", "蟲害", "初生本葉時幼蟲咬食葉片，蟲體長大後為害大片葉面，果實長出後危害果面及果肉",
     "性費洛蒙緩釋劑誘蟲盒或蘇力菌防治",
     "農業知識入口網（苦瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=38105", "official", "2026-08-19"),

    # 芋頭 - 農業知識入口網 芋頭病蟲害防治主題館 subject id=18996（官方，節選4項）
    ("yutou", "軟腐病", "病害", "葉形變小，生育停滯，芋塊莖由下而上逐漸變黑而腐敗",
     "栽培抗病品種（如高雄一號）、實施水旱田輪作、選用健康苗",
     "農業知識入口網（芋頭主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18996", "official", "2026-08-19"),
    ("yutou", "疫病", "病害", "葉片上生出黃褐色圓形斑點，逐次擴大，表面出現同心輪紋，可造成90%以上葉片枯凋",
     "27.12%三元硫酸銅水懸劑稀釋800倍",
     "農業知識入口網（芋頭主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18996", "official", "2026-08-19"),
    ("yutou", "長角象鼻蟲", "蟲害", "幼蟲蛀食成隧道狀，傷口易為軟腐病原菌侵入",
     "後期保持土壤濕潤",
     "農業知識入口網（芋頭主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18996", "official", "2026-08-19"),
    ("yutou", "福壽螺", "蟲害", "危害芋苗，為水芋栽培常見問題",
     "80%聚乙醛可濕性粉劑每公頃1.2公斤，或苦茶粕每分地10～15公斤",
     "農業知識入口網（芋頭主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=18996", "official", "2026-08-19"),

    # 薑
    ("jiang", "薑青枯病", "病害", "細菌性病害，切開莖部維管束有褐變現象，莖部剖面置於清水中可見乳白色雲霧狀菌泥自切面流出",
     "參考植物保護手冊防治方法，選用健康種薑、避免連作",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7287", "official", "2026-08-19"),
    ("jiang", "薑軟腐病", "病害", "真菌性病害，清水中無乳白色物流出，危害處表面可見白色菌絲",
     "參考植物保護手冊防治方法，選用健康種薑、避免連作",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7287", "official", "2026-08-19"),

    # 韭菜
    ("jiucai", "薊馬", "蟲害", "以口器挫吸葉片留下白色條斑狀食痕，形成細密長形灰白色斑點，嚴重時葉枯黃",
     "辣椒水稀釋噴施；搭配黃色黏蟲紙；使用天敵（小黑花椿象）；或選購殺薊馬殺蟲劑噴施",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=5684", "official", "2026-08-19"),
    ("jiucai", "白絹病", "病害", "初發病於株莖基部呈水浸狀病斑，罹病株倒伏、葉片枯萎，長出白色棉狀菌絲體",
     "參考植物保護手冊防治方法",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=5684", "official", "2026-08-19"),

    # 蔥
    ("cong", "紫斑病", "病害", "被害葉初呈淡褐色小型病斑，擴大成紡錘狀後凹陷為暗紫色紡錘型病斑，邊緣淡紅色至淡紫色，病斑上產生黑色黴狀物同心輪，常因帶狀乾枯而折斷；發病適溫25℃，需雨水或持續露水期侵入，亦可危害大蒜及洋蔥",
     "參考植物保護手冊防治方法",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7320", "official", "2026-08-19"),

    # 西瓜
    ("xigua", "銀葉粉蝨", "蟲害", "成蟲及若蟲群集葉背吸食，嚴重時葉片黃化，分泌蜜露誘發煤煙病，並傳播瓜類退綠黃化病毒與南瓜捲葉菲律賓病毒",
     "注意田間衛生、減少中間寄主或雜草；植株頂端30公分內懸掛黃色黏板誘殺；每葉葉背超過2隻成蟲需加強防治；適當疏蔓疏葉、氮肥不宜過多；藥劑輪用並噴到葉背",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=404457", "official", "2026-08-19"),

    # 芒果
    ("mangguo", "炭疽病", "病害", "危害果實、花穗、嫩葉及嫩梢；葉片初期紅色小斑點逐漸擴大呈褐色致葉片扭曲皺縮；花梗變黑褐色小花脫落；幼果出現紅色小斑點後擴大呈不規則黑點，後熟時形成黑色凹陷不規則病斑",
     "果園勿雜植高大土芒果；剪除嚴重罹病枝葉並清除落葉落果；修剪枝梢後施用10-10式波爾多液1～2次；4-5月人工疏果或生理落果結束後即行套袋；新梢及開花期加強藥劑防治，降雨後補強施藥",
     "農業知識入口網（芒果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=57003", "official", "2026-08-19"),

    # 花生
    ("huasheng", "銹病", "病害", "由Puccinia arachidis引起，主要危害葉片及葉柄，病斑葉背最多；初期葉表出現黃色小斑，葉背形成夏孢子堆（初黃橙色後轉深褐色），釋出鏽色粉末隨風傳播；嚴重時葉片黃化萎凋、落葉，莢果不飽滿，秋作受害最嚴重",
     "參考植物保護手冊防治方法",
     "農業知識入口網（落花生主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=27936", "official", "2026-08-19"),
    ("huasheng", "白絹病", "病害", "常發生於晚春作及早秋作生育期，高溫多濕時加重；造成種子腐爛、出土後幼苗死亡，地下莢果及果柄褐化腐爛，患部長出白色絹狀菌絲，土表出現放射狀菌絲束，後期形成白色菌核並轉褐色，嚴重時損失可達80%以上",
     "參考植物保護手冊防治方法",
     "農業知識入口網（落花生主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=27938", "official", "2026-08-19"),

    # 百香果
    ("baixiangguo", "果實蠅", "蟲害", "俗稱蜂仔，成蟲白晝活動，清晨後取食產卵，中午於樹間陰涼處棲息，下午3-4點後再活動，繁殖力強，短期內族群迅速增長，造成落果及腐爛失去商品價值",
     "含毒甲基丁香油誘殺劑滅雄，須全年全面實施才有效；結果期噴施33%福木松乳劑或50%芬殺松乳劑1000倍，每7～10天施藥一次，採收前12天停止使用；利用寄生蜂等天敵防治幼蟲及蛹",
     "農業知識入口網（百香果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40183", "official", "2026-08-19"),

    # 龍眼
    ("longyan", "龍眼木蝨", "蟲害", "一年約發生7個世代，成蟲於嫩梢嫩葉或葉背吸食汁液，造成嫩梢乾枯，葉背棲息處凹陷、葉面對應處突起，嚴重時葉片捲曲變形枯黃落葉，影響樹勢及果實產量品質",
     "採後修剪維持樹冠透光通風，修剪枝條集中帶離果園減少越冬蟲源；加強水分肥料管理增強樹勢避免抽梢不一致；保護天敵（寄生蜂、草蛉、盲椿）加強生物防治",
     "農業知識入口網（龍眼主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=44975", "official", "2026-08-19"),

    # 酪梨
    ("laoli", "炭疽病", "病害", "新梢嫩葉尚未轉綠前極易感染，初期紅色小針點逐漸擴大為近圓形褐色斑外圍有黃暈；幼果受侵染留下黑色小斑點，具潛伏感染特性，直到果實成熟病斑才擴大；高溼度、陰雨連綿或颱風季節好發，傷口增加侵入機會",
     "參考芒果炭疽病防治，清園並提早套袋，清理地面落葉，噴藥降低病原菌密度；尚無專門推薦藥劑，可參考植物保護手冊用於鳳梨、木瓜及香蕉之藥劑",
     "農業知識入口網（酪梨主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=25574", "official", "2026-08-19"),

    # 番茄
    ("fanqie", "晚疫病", "病害", "由致病疫霉(Phytophthora infestans)引起，性喜冷涼潮濕氣候，可危害葉、葉柄、莖、花序及果實，初呈水浸狀圓形或不規則病斑，濕度大或降雨時病斑迅速擴大成灰褐色壞疽斑，周邊長出白色黴狀物；發病適溫約20℃、相對濕度95%以上；花蓮宜蘭地區冬春季東北季風期間低溫多濕好發",
     "塑膠布設施栽培加強田間衛生管理；噴施可誘導抗病的中性亞磷酸溶液；藥劑防治",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=19977", "official", "2026-08-19"),
    ("fanqie", "早疫病", "病害", "主要危害葉片，初呈水漬狀綠色病斑，持續惡化出現同心輪紋，嚴重時葉片枯死；好發於高溫多濕季節，溫度25～30℃、空氣濕度高時易發生",
     "參考植物保護手冊防治方法",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=3778", "official", "2026-08-19"),

    # 胡瓜（花胡瓜）
    ("hugua", "露菌病", "病害", "由Pseudoperonospora cubensis引起，影響瓜類作物包含胡瓜", "參考植物保護手冊防治方法，設施栽培屋頂覆蓋透明塑膠布可阻擋雨水傳播", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8696", "qa", "2026-08-19"),
    ("hugua", "炭疽病", "病害", "由Colletotrichum gloeosporioides引起，主要危害葉片，初期近葉脈處出現褐黃色圓形病斑", "參考植物保護手冊防治方法", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8696", "qa", "2026-08-19"),

    # 辣椒
    ("lajiao", "炭疽病", "病害", "好發於高溫多雨季節，最適發病溫度25～28℃，分生孢子藉雨水飛濺或灌溉水傳播；病原菌於開花期或幼果期感染，至果實成熟後才顯現病徵，嚴重時可造成50%以上產量損失",
     "有機防治可用亞磷酸1,000倍混合枯草桿菌500倍及苦楝油500倍，每3天一次連續三次，建議5～10月每月防治一次",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18552", "qa", "2026-08-19"),
    ("lajiao", "病毒病", "病害", "有多種花葉病及壞死病，為辣椒栽培中危害較重的病害之一", "防治傳播媒介昆蟲（蚜蟲、薊馬等）", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=18552", "qa", "2026-08-19"),

    # 秋葵
    ("qiukui", "二點小綠葉蟬", "蟲害", "成蟲及若蟲棲息葉背，刺吸葉液造成葉片捲曲萎縮及焦枯，葉片由邊緣呈淡黃色逐漸枯萎，造成植株衰弱", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10018", "qa", "2026-08-19"),
    ("qiukui", "薊馬", "蟲害", "以口器吸食葉片、花果，受害初期呈銀白色小斑點，情況惡化後轉為褐色傷口", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10018", "qa", "2026-08-19"),

    # 洋香瓜
    ("yangxiangua", "白粉病", "病害", "設施栽培最常見病害，葉片、葉柄、新蔓上出現白色粉狀物，後期轉灰色並產生黑色顆粒狀子囊殼", "物理防治如噴水；礦物油400～500倍稀釋；化學藥劑防治需輪用避免抗藥性", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7311", "qa", "2026-08-19"),
    ("yangxiangua", "蔓枯病", "病害", "主要發生於莖基部，初呈水浸狀病斑，後組織壞死變黑並產生膠質裂痕，為洋香瓜主要病害之一，嚴重時損失慘重", "參考植物保護手冊防治方法", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7311", "qa", "2026-08-19"),

    # 山藥
    ("shanyao", "炭疽病", "病害", "由Gloeosporium sp.及Colletotrichum sp.引起；北台灣山藥栽培區主要病害還包含灰黴病、葉斑病、萎凋病、白絹病、晚疫病、病毒病及線蟲", "參考山藥病害防治主題館防治方法", "農業知識入口網（山藥主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=33786", "official", "2026-08-19"),

    # 蘆筍
    ("lusun", "莖枯病", "病害", "沿莖生出紡錘形或線狀暗褐色病斑，周緣水浸狀，病斑可達0.2～0.5×2～3公分，病斑圍繞莖枝使上部乾枯而死呈火燒狀；高濕由雨水霧露使孢子釋放傳播感染健康組織",
     "清除田間病株殘留物及雜草；藥劑防治（免賴得、保利黴素、腐絕、鋅錳乃浦等）",
     "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30071", "official", "2026-08-19"),
    ("lusun", "莖腐病", "病害", "主要危害幼筍，莖表出現水浸狀斑駁進而腐爛崩潰", "加強田間排水；清除病株", "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30071", "official", "2026-08-19"),
    ("lusun", "立枯病", "病害", "植株黃化、矮化、萎凋而枯死，根部維管束褐化", "選用抗病品種；改善排水；廢耕轉作3～5年以上", "農業知識入口網（蘆筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=30071", "official", "2026-08-19"),

    # 咖啡
    ("kafei", "咖啡銹病", "病害", "初期上葉表淡黃色小斑點，下葉表有橘黃色夏胞子堆自氣孔長出，後期佈滿病斑中心漸乾枯成褐色，通常下位葉先發病再向上蔓延；減少光合量導致減產15～20%，嚴重達70%，造成提早落葉或全株枯死；夏胞子需連續24～48小時游離水才能發芽感染，多在雨季感染，發病溫度15～28℃",
     "選擇日照良好栽培地；適當調整氮磷肥、減少鉀肥；寬行栽植與適當修剪增加通風；控制每棵樹結果節在230節以下；控制雜草並嚴格清園；國外用銅劑可防治但國內尚未有推薦農藥",
     "農業知識入口網（咖啡主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=45565", "official", "2026-08-19"),
    ("kafei", "咖啡果小蠹", "蟲害", "學名Hypothenemus hampei，雌蟲以咀嚼式口器於咖啡果實臍部鑽食小圓孔，蛀食果實內部胚，造成果實無法成熟或成熟果實滿佈蛀孔，生豆含水量高於12%時儲存期間會繼續蛀食",
     "使用誘殺器監測發生密度或大量誘殺（台南區農業改良場與茶葉改良場已開發）；清除園區內被害果",
     "農業知識入口網（咖啡主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=45584", "official", "2026-08-19"),

    # 牛蒡
    ("niupang", "切根蟲／甜菜夜蛾／斜紋夜盜", "蟲害", "牛蒡主要蟲害種類，另有番茄斑潛蠅及光褐菊蚜", "性費洛蒙誘殺（每公頃設5～10個點長期誘殺）；化學藥劑防治以傍晚噴藥效果最佳", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=115", "qa", "2026-08-19"),

    # 紅豆
    ("hongdou", "豆類花薊馬", "蟲害", "對紅豆威脅最大的蟲害，必須於開花期特別注意防範", "參考安全用藥紅豆病蟲害防治用藥表、植物保護手冊豆類部分或紅豆TGAP病蟲草害防治曆", "農業知識入口網（紅豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39711", "official", "2026-08-19"),
    ("hongdou", "白粉病", "病害", "紅豆較常見病害之一", "參考安全用藥紅豆病蟲害防治用藥表", "農業知識入口網（紅豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39711", "official", "2026-08-19"),
    ("hongdou", "根腐病", "病害", "低濕地區易發生", "參考植物保護手冊豆類部分", "農業知識入口網（紅豆主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39711", "official", "2026-08-19"),

    # 玉米
    ("yumi", "玉米銹病", "病害", "普通型銹病病斑多見於葉片、葉鞘及苞葉，初期表皮覆蓋數天後破裂產生咖啡色粉末狀孢子，後期形成深褐至黑色孢子堆；南方型銹病病斑密集小圓形(直徑0.2～0.5公厘)、金黃色，多發生於生長中後期",
     "栽培抗病品種；11.8%護汰芬水懸劑稀釋2000倍，發病初期開始每10天施藥一次共4次；或45.5%待普利乳劑稀釋5000倍，發病時施藥後每7～10天再施連續3次",
     "農業知識入口網（玉米主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=31684", "official", "2026-08-19"),
    ("yumi", "玉米螟", "蟲害", "學名Ostrinia furnacalis，北部一年3～4代、南部7～8代，南部因周年栽培整年可找到寄主",
     "發芽後20～25天開始釋放蜂片，每隔6～7天釋放一次連續4次（每次每公頃150片）；拔除全園1/2～3/5雄花斷絕初齡幼蟲食物；藥劑可選蘇力菌製劑、諾伐隆乳劑、加保利等",
     "農業知識入口網（玉米主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=31697", "official", "2026-08-19"),

    # A菜（萵苣）
    ("azhai", "萵苣蚜蟲", "蟲害", "葉片顏色變淡或呈灰綠色且變形，受害萵苣不具賣相；嚴重時植株停止生長；會傳播葉脈帶狀病毒、花椰菜花葉病毒及小黃瓜花葉病毒；侵入結球萵苣內部後施藥不易滅除，且易對藥劑產生抗性",
     "定期且有效的藥劑防治可將損失控制在10%以下；抗性育種；施放草蛉及捕食性昆蟲進行生物防治",
     "農業知識入口網（萵苣主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=8651", "official", "2026-08-19"),

    # 皇宮菜（落葵）
    ("huanggongcai", "斑點病", "病害", "生長勢強健、少有病蟲害，僅老化葉片會發生斑點病，雨天葉子容易受損產生斑點", "落葵抵抗力強，栽培期間可完全不使用農藥", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13106", "qa", "2026-08-19"),

    # 龍鬚菜
    ("longxucai", "蔓枯病", "病害", "龍鬚菜生命力強健、種植時較少病蟲害，但採用畦作栽培時比棚架栽培容易感染蔓枯病", "採棚架栽培較能降低感染風險", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8735", "qa", "2026-08-19"),

    # 菠菜
    ("bocai", "立枯病", "病害", "病原菌為Rhizoctonia solani、Pythium sp.及Fusarium sp.；菠菜蟲害冬天較少，病害則因雨水較嚴重", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=city_farming&id=98", "qa", "2026-08-19"),

    # 芥菜
    ("jiecai", "黃葉病", "病害", "十字花科蔬菜重要病害，植株生長任何階段皆可能發生，近基部根維管束變色並逐漸腐敗，導致植株生長不良不適合醃漬", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "qa", "2026-08-19"),
    ("jiecai", "番茄斑潛蠅／小菜蛾", "蟲害", "與黃葉病並列為芥菜最重要的病蟲害，嚴重時可能導致棄耕", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=1497", "qa", "2026-08-19"),

    # 九層塔
    ("jiucengta", "露菌病", "病害", "由Peronospora belbahrii引起，冷涼高濕環境易感染，感染初期葉片黃化及輕微皺縮扭曲，隨後背面產生黑褐色絨毛狀物", "移除病葉；避免傍晚澆水", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9403", "qa", "2026-08-19"),
    ("jiucengta", "蚜蟲", "蟲害", "聚集嫩葉處吸食汁液，導致葉子捲曲變形；另有軍配蟲、薊馬、葉蟎等造成葉片白斑", "葵無露或苦楝油於清晨或傍晚氣溫較涼時噴施；蚜蟲天敵以瓢蟲最常見，可利用生物防治", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13602", "qa", "2026-08-19"),

    # 山蘇
    ("shansu", "介殼蟲與軟體動物", "蟲害", "自然環境下山蘇少有重大病蟲害，但近年林下、檳榔園下大量種植且多不施農藥，一旦發生易滋生蔓延；介殼蟲、蝸牛、蛞蝓等軟體動物為害最普遍，蝸牛蛞蝓對產量影響最大",
     "另有豆芫菁、螟蛾類、根蟎、螽斯及蝗蟲類等蟲害，及真菌細菌線蟲類病害",
     "農業知識入口網（山蘇主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=22725", "official", "2026-08-19"),

    # 地瓜（甘藷塊根，與地瓜葉為同株植物，病蟲害資料相同）
    ("digua", "甘藷蟻象", "蟲害", "危害塊根，為甘藷最常見害蟲", "每公頃施用2.5%陶斯松粉劑45公斤於莖蔓間，間隔7～10天施用一次，連續3～4次；另可設置性費洛蒙誘蟲盒", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19321", "official", "2026-08-19"),
    ("digua", "甘藷蔓割病", "病害", "生育期病害之一（與縮芽病、簇葉病、病毒病並列），採收後貯藏期另有軟腐病及炭化病", "輪作；浸水處理；藷苗浸藥處理", "農業知識入口網（甘藷主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=19321", "official", "2026-08-19"),

    # 豌豆
    ("wandou", "豌豆立枯病", "病害", "台灣夏秋季豌豆栽培的主要限制因子，屬重要的土壤傳染性病害", "參考植物保護手冊防治方法，避免夏秋季連作", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/index.php?id=145", "qa", "2026-08-19"),
    ("wandou", "薊馬類", "蟲害", "豌豆栽培最重要的限制因子，栽培密度高或過早栽培（乾燥高溫）環境易使薊馬高密度發生；另有甜菜夜蛾、斑潛蠅危害", "參考植物保護手冊防治方法，避免過早栽培於乾燥高溫環境", "農業知識入口網（豌豆主題館）", "https://kmweb.moa.gov.tw/subject/index.php?id=145", "qa", "2026-08-19"),

    # 油菜
    ("youcai", "軟腐病", "病害", "組織最初出現水浸狀小斑點，快速加深加寬，病組織軟化變色起皺並裂開流出黏稠液體，產生硫磺臭味", "避免密植維持通風與排水，拔除銷毀病株；施用12.5%鏈黴素溶液1000倍；施用殺蟲劑防治媒介昆蟲；採收避免傷口並低溫低濕保存", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2630", "official", "2026-08-19"),

    # 大蒜
    ("dasuan", "赤銹病／病毒病／黃萎病", "病害", "大蒜主要病害，赤銹病(銹病)危害葉片，病毒病與黃萎病亦為常見問題", "參考植物保護手冊防治方法", "農業知識入口網（大蒜主題館）", "https://kmweb.moa.gov.tw/subject/index.php?id=56289", "qa", "2026-08-19"),

    # 蓮藕
    ("lianou", "福壽螺", "蟲害", "1979年自阿根廷引進台灣後棄養擴散，危害水芋、蓮花、空心菜等水生作物；4～11月高溫多雨季節活躍，食量大繁殖快，積水時危害最嚴重，啃食葉柄葉片及外露塊莖", "參考植物保護手冊防治方法，注意田間積水管理", "農業知識入口網", "https://kmweb.moa.gov.tw/subject/subject.php?id=31960", "official", "2026-08-19"),

    # 薑黃
    ("jianghuang", "炭疽病", "病害", "危害莖、葉", "發病初期噴50%多菌靈可濕性粉劑500倍液，每旬噴1次", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=10505", "qa", "2026-08-19"),

    # 香菜（芫荽）
    ("xiangcai", "蚜蟲／白粉虱／葉蟎", "蟲害", "常見害蟲，吸食植物汁液，導致葉片枯黃或變形；葉片柔嫩容易因雨水造成傷害", "肥皂水噴灑物理清除；保持良好通風與適當灌溉減少滋生；嚴重時可用瓢蟲等生物防治", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=4516", "qa", "2026-08-19"),

    # 甘蔗
    ("ganzhe", "螟蟲（鑽心蟲）", "蟲害", "為害普遍而嚴重，幼蟲鑽入甘蔗幼苗和蔗莖，苗期入侵生長點造成枯心苗，生長中後期入侵蔗莖形成蟲孔節破壞組織使糖分降低；主要有黃螟、條螟、二點螟、大螟、白螟等5種", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2377", "qa", "2026-08-19"),

    # 胡麻（芝麻）
    ("huma", "芝麻莢野螟", "蟲害", "學名Antigastra catalaunalis，胡麻主要害蟲之一", "參考胡麻主題館病蟲害防治藥劑資訊", "農業知識入口網（胡麻主題館）", "https://kmweb.moa.gov.tw/subject/index.php?id=163", "official", "2026-08-19"),
    ("huma", "菸盲椿象", "蟲害", "學名Nesidocoris tenuis，胡麻常見害蟲之一", "參考胡麻主題館病蟲害防治藥劑資訊", "農業知識入口網（胡麻主題館）", "https://kmweb.moa.gov.tw/subject/index.php?id=163", "official", "2026-08-19"),

    # 小米
    ("xiaomi", "葉銹病", "病害", "真菌性病害，葉片正反兩面及葉鞘、稈出現大量褐色夏孢子，病菌以冬孢子在病株殘體上越冬，藉雨水昆蟲風媒傳播；多雨、高溫高濕及氮肥過多時易發病",
     "種植抗病品種；合理施肥",
     "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32244", "official", "2026-08-19"),
    ("xiaomi", "粟灰螟", "蟲害", "幼蟲於苗基部葉鞘蛀入莖內，5天後苗心葉枯萎，蛀莖4天後開始從洞孔排出蟲糞殘屑，一隻幼蟲可轉移危害3～4株幼苗",
     "釋放赤眼卵寄生蜂等天敵；使用蘇力菌微生物製劑",
     "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32237", "official", "2026-08-19"),
    ("xiaomi", "粟夜盜蟲", "蟲害", "咬斷穗部、啃食葉莖，5～6齡為暴食階段危害最嚴重",
     "中耕除草撿拾卵塊；廢園翻犁及灌水；燈光或性費洛蒙誘殺；釋放寄生蜂或使用蘇力菌、核多角體病毒",
     "農業知識入口網（小米及台灣藜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=32237", "official", "2026-08-19"),

    # 荔枝
    ("lizhi", "荔枝椿象", "蟲害", "學名Tessaratoma papillosa，俗稱臭屁蟲，以刺吸方式危害荔枝、龍眼，導致落花落果、嫩枝幼果枯萎，並引起荔枝酸腐病；為害常造成20～30%損失，嚴重達80～90%產量損失；成蟲若蟲亦傳播龍眼鬼帚病",
     "台灣本島目前為非疫區（僅金門曾發現危害）；荔枝及龍眼盛花期應停止施藥以免傷害授粉昆蟲，其餘時期可參考植物保護手冊防治",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=2898", "official", "2026-08-19"),

    # 蓮霧
    ("lianwu", "東方果實蠅", "蟲害", "台灣果樹最重要害蟲，寄主包含蓮霧、芭樂、柑橘、芒果、楊桃、梨、桃、釋迦、棗、龍眼、荔枝、柿等；雌蟲產卵於果實，幼蟲蛀食造成表面出油、果實腐爛甚至提早落果，使果實失去商品價值",
     "清園移除落果；套袋阻絕；懸掛含毒甲基丁香油誘殺器誘殺雄蟲",
     "農業知識入口網（蓮霧主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=2319", "official", "2026-08-19"),

    # 木瓜
    ("mugua", "輪點病毒病", "病害", "俗稱「狂株」，1975年首見於高雄燕巢，由有翅蚜蟲及機械傳播、迅速蔓延；心葉黃化縮小，葉背水浸狀輪狀或點狀病斑，病葉變小葉緣乾枯脫落，僅剩頂端新葉甚至全脫落致死；花瓣果實出現油浸狀斑紋輪紋，開花不能結果或果實品質差",
     "網室栽培；栽植耐病品種台農五號；苗接種弱毒交互保護；套袋並間作玉米；避免園內及附近栽植西瓜南瓜胡瓜甜瓜等中間寄主瓜類；接觸病株的手與工具用肥皂水洗滌；儘早拔除病株深埋或燒毀",
     "農業知識入口網（木瓜主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=8200", "official", "2026-08-19"),

    # 鳳梨
    ("fengli", "心腐病", "病害", "由Phytophthora spp.引起，雨季高溫時嚴重，主要危害新植苗或幼株，造成萎凋葉片轉紅下垂甚至倒伏，縱切病株心葉組織呈褐色腐爛並有白色菌絲及霉味，病健交界處有深褐色暈環",
     "參考植物保護手冊防治方法，注意排水避免積水",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?func=1&type=432&id=7028", "official", "2026-08-19"),

    # 葡萄
    ("putao", "露菌病", "病害", "由Plasmopara viticola引起，葉下表皮產生白色黴狀物胞囊、葉上表皮產生維管束侷限型病斑，亦感染枝條捲鬚花及幼果，幼果感染後萎縮並產生胞囊傳播鄰近果實；好發16～28℃，胞囊藉風雨傳播，相對濕度85%以下無法順利產生胞囊，高濕多雨環境利於發展",
     "參考植物保護手冊防治方法，注意田間通風排水",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=393397", "official", "2026-08-19"),
    ("putao", "黑痘病", "病害", "好發於梅雨期及夏季，隨雨露水傳染，危害新梢、葉片、花穗", "參考植物保護手冊防治方法", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledgebase.php?id=393397", "qa", "2026-08-19"),

    # 草莓
    ("caomei", "炭疽病", "病害", "近年躍升草莓育苗期頭號殺手，好發高溫多濕環境，病原菌包含Colletotrichum gloeosporioides、C. fragariae、C. acutatum等", "參考植物保護手冊防治方法，育苗期加強通風降低濕度", "農業知識入口網", "https://kmweb.moa.gov.tw/theme_data.php?theme=agri_book&id=2140", "qa", "2026-08-19"),

    # 甜柿
    ("tianshi", "炭疽病", "病害", "病原菌Colletotrichum gloeosporioides，感染幼嫩葉片、枝條及果實；嫩枝染病初期出現黑色斑點，後擴展為2公分長紡錘型病斑，皮層凹陷龜裂嚴重時枝枯；果實轉色期出現圓形至橢圓形深褐色病斑；全年可發生，3～4月高濕環境發病轉劇烈",
     "整枝修剪去除病枝減少感染源；果樹萌芽時噴施25%撲克拉乳劑2000倍，之後每隔2星期施藥一次，採收前9天停止施藥",
     "農業知識入口網（甜柿主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=7694", "official", "2026-08-19"),

    # 釋迦
    ("shijia", "東方果實蠅", "蟲害", "年約發生8～9世代，7～9月發生密度較高，雌蟲選擇黃熟果實產卵，幼蟲於果肉內蛀食致使果實腐爛及落果",
     "清園撿除落果；套袋阻絕法；懸掛含毒甲基丁香油誘燈誘殺雄蠅",
     "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6342", "official", "2026-08-19"),

    # 柑橘
    ("ganju", "介殼蟲類", "蟲害", "黑點介殼蟲死後緊密貼附於枝葉或果實上不易脫落；褐圓介殼蟲使枝葉萎縮變黃而凋落", "44%大滅松乳劑稀釋1000倍噴施", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2823", "official", "2026-08-19"),
    ("ganju", "蚜蟲類", "蟲害", "成蟲及若蟲群集新梢嫩葉吸食汁液，被害新葉捲縮", "44%大滅松乳劑稀釋1000倍噴施", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2823", "official", "2026-08-19"),
    ("ganju", "柑橘木蝨", "蟲害", "成蟲及若蟲群集新梢嫩葉吸食汁液，被害嫩梢枝條常呈畸形", "44%大滅松乳劑稀釋1000倍噴施", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2823", "official", "2026-08-19"),
    ("ganju", "潛葉蛾", "蟲害", "幼蟲孵化後蛀入嫩葉葉肉危害，形成中空曲折隧道，新葉捲縮不展", "24%納乃得可濕性粉劑稀釋750倍", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2823", "official", "2026-08-19"),
    ("ganju", "星天牛", "蟲害", "幼蟲先繞皮層內側盤食後蛀食木質部，被害株葉片黃化凋落", "成蟲出現時每隔一個月將40.64%加保扶水懸劑100倍藥液噴灑於離地面45公分之樹幹基部", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2823", "official", "2026-08-19"),

    # 香蕉
    ("xiangjiao", "香蕉黃葉病", "病害", "病原菌Fusarium oxysporum f.sp cubense (FOC)，俗稱Panama disease；下方老葉葉緣先黃化擴大至中肋，葉柄軟化彎曲下垂後枯萎，上方幼葉逐漸變黃終至整株枯萎死亡；假莖或塊莖縱切可見維管束呈黃色至褐色，後期貫穿成長條形", "參考植物保護手冊防治方法，選用抗病品種、避免病區種苗", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8043", "qa", "2026-08-19"),
    ("xiangjiao", "香蕉葉斑病", "病害", "危害全球香蕉產區最嚴重病害之一，初期第3或4片葉背面出現紅棕色小條斑，後擴大變黑並出現於葉表面，後期轉黑褐色或黑色病斑，受害葉片提早枯死，影響健葉數導致產期延後或減產；目前僅侷限東部台東關山至花蓮壽豐、西部高雄美濃至台南楠西零星發生", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8043", "qa", "2026-08-19"),

    # 楊桃
    ("yangtao", "褐根病", "病害", "楊桃主要病害之一，會導致楊桃樹死亡", "田間衛生管理，定期清除銷毀病葉病枝落果；避免自病區取得嫁接材料或苗木；生理落葉期、修剪後、雨季前預防性施藥；已感染果園需重剪病枝葉後每週噴藥連續5～6次，雨季加強噴藥", "農業知識入口網（楊桃主題館）", "https://kmweb.moa.gov.tw/subject/index.php?id=26", "qa", "2026-08-19"),

    # 檸檬
    ("ningmeng", "柑橘潛葉蛾", "蟲害", "全年皆有危害，2～7月危害普遍較嚴重；卵產於植物表皮內，孵化幼蟲於表皮內鑽孔挖道取食，葉片上形成不規則圖形", "參考檸檬常見重要蟲害及有害動物防治介紹", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=16623", "qa", "2026-08-19"),

    # 冬瓜
    ("donggua", "灰黴病", "病害", "生育期皆可危害花及果實，形成褐色水浸狀病斑及灰褐色黴狀物", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13935", "qa", "2026-08-19"),
    ("donggua", "黑點病", "病害", "危害果實及葉片", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=13935", "qa", "2026-08-19"),

    # 馬鈴薯
    ("malingshu", "晚疫病", "病害", "由Phytophthora infestans引起，藉風雨飛濺或人畜攜帶短時間內長距離傳播；台灣冬季16～22℃、相對濕度90～95%以上維持4～6小時以上易發病；被害部位水浸狀黑褐化，感染部位以上組織枯萎，嚴重時全株如火燒狀焦枯死亡",
     "健康種薯、抗（耐）病品種與田間衛生病害管理為綜合防治重要環節",
     "農業知識入口網（馬鈴薯主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39768", "official", "2026-08-19"),
    ("malingshu", "瘡痂病", "病害", "由植物病原細菌放射線菌Streptomyces scabies引起，存活於土壤和罹病薯塊中，主要由皮目侵入亦可經傷口侵入；薯球表面出現近圓形或不定形木栓化瘡痂狀褐色病斑或疣狀斑塊，嚴重時病斑癒合呈網狀龜裂，影響外觀品質與貯藏性能；薯球膨大後期水分管理不當容易感染",
     "注意薯球膨大期水分管理",
     "農業知識入口網（馬鈴薯主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39771", "official", "2026-08-19"),

    # 大白菜
    ("dabaicai", "軟腐病", "病害", "病斑初呈水浸狀小點，迅速擴大，組織軟化變色起皺腐爛裂開流出汁液，導致結球腐爛；常與病毒病、霜霉病並稱大白菜三大病害", "參考植物保護手冊防治方法", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=5164", "qa", "2026-08-19"),
    ("dabaicai", "根蛆", "蟲害", "大白菜種蠅幼蟲，咬傷菜根後病菌乘機侵入，引起掉幫腐爛", "根際施用草木灰；長至6～8葉時用草木灰、石灰和2.5%敵百蟲粉混合撒施於菜根四週", "農業知識入口網（使用者問答）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=5164", "qa", "2026-08-19"),

    # 茭白筍（黑穗菌與茭白筍為共生關係，此處記錄其特殊性質而非單純病害防治）
    ("jiaobaisun", "黑穗菌（形成茭白筍的共生真菌）", "病害", "茭白筍食用部位即因黑穗菌寄生刺激莖部細胞增殖膨大而形成的「病態莖」，18～25℃適溫下菌絲生長並產生細胞生長素刺激膨大；若採收過晚孢子成熟，筍肉內出現大量黑色斑點（俗稱「灰茭」），影響賣相與食慾",
     "須在莖部膨大但孢子尚未成熟前適時採收，避免延遲採收形成灰茭",
     "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=31915", "official", "2026-08-19"),

    # 四季豆
    ("sijidou", "銹病", "病害", "台灣長期多雨潮濕氣候提供理想發病條件，適溫18～26℃，春秋兩季特別嚴重；主要危害葉片偶見豆莢與莖，初期葉背出現白色小斑點，逐漸擴大為銹色隆起圓形斑，導致葉片黃化提早脫落，影響光合作用降低產量品質",
     "參考植物保護手冊防治方法",
     "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=8529", "qa", "2026-08-19"),

    # 青花菜
    ("lvhuaqielan", "紋白蝶／小菜蛾", "蟲害", "十字花科蔬菜常見鱗翅目害蟲，紋白蝶幼蟲喜食十字花科葉片；小菜蛾幼蟲受驚後有吐絲下垂習性，俗稱「吊絲蟲」", "田間附近種植馬利筋或金露花吸引瓢蟲草蛉椿象等天敵；螟蛾類為害可種單瓣扶桑花利於蜘蛛寄生蜂棲息", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=6934", "qa", "2026-08-19"),

    # 火龍果
    ("huolongguo", "莖潰瘍病", "病害", "病原菌Neoscytalidium dimidiatum，果實初現白色凹陷圓斑(1.0-1.5mm)逐漸擴大，病斑中央出現小紅點，多個病斑癒合成大片褐色塊斑，罹病組織表面出現褐色結痂硬塊容易龜裂，果實褐色軟化逐漸轉黑並產生黑色針狀產孢構造；莖部白色斑點中央紅點擴大突起，病斑周圍木栓化長出黑色小點，高濕時周圍組織黃色潰爛；為高溫菌30℃危害較嚴重，好發5～9月雨季",
     "選用健康無病害枝條種植於新植地；11月至翌年3月乾冷季節清園並用4-4式波爾多液保護新生枝條（此時病原菌最虛弱防治最有效率）；藥劑可用得克利、甲基多保淨、賽普護汰寧等；合理化施肥減少氮肥、提前套袋",
     "農業知識入口網（紅龍果主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=39779", "official", "2026-08-19"),

    # 菱角
    ("lingjiao", "福壽螺", "蟲害", "1979年自阿根廷引進台灣後棄養，1982年首見危害高屏地區新植稻苗，隨後發現危害菱角、水芋、空心菜、蓮花等水生經濟作物，每年危害逾10萬公頃農地；偏好取食嫩莖部位，水溫低（約15℃）或濕度不足時活動力降低",
     "田間進水口裝鐵網阻隔螺類進入水溝；排水口放置30公分塑膠浪板防止螺類進入田區；人工摘除卵塊並撿拾螺體；田埂周圍每公頃施用茶粕50公斤；使用苦楝萃取物製成的「移護螺」粒劑每公頃10～15公斤；有機田可養鴨協助清除",
     "農業知識入口網（茭白筍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=31961", "official", "2026-08-19"),

    # 蘋果
    ("pingguo", "銹病", "病害", "發生於葉片及枝條，初呈橢圓形隆起病斑，形成夏孢子堆後轉橙黃色並釋出鏽褐色粉末狀夏孢子，台灣好發高峰期為1～6月", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9850", "qa", "2026-08-19"),
    ("pingguo", "蚜蟲", "蟲害", "有翅與無翅型，孤雌生殖繁殖快速，群集葉背及枝梢吸食汁液造成黃化萎凋，分泌蜜露誘發煤煙病，並可能傳播病毒病", "肥皂水噴灑葉背（酒精會傷害蘋果樹不建議使用）", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9850", "qa", "2026-08-19"),

    # 豇豆（長豆）
    ("jiangdou", "萎凋病", "病害", "長豇豆受萎凋病威脅嚴重，「見錢死」使國內種植面積從98年1,353公頃大幅下降；另有白絹病、瓜實蠅及薊馬等常見病蟲危害", "高雄區農業改良場已推出2.0版抗病根砧嫁接苗，抗病力逾96%、增產可達45%", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=169", "qa", "2026-08-19"),
    ("jiangdou", "銹病", "病害", "豇豆／四季豆常見病害之一", "參考植物保護手冊防治方法", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/theme_data.php?theme=production_map&id=169", "qa", "2026-08-19"),

    # 皇帝豆（萊豆）
    ("huangdidou", "蚜蟲", "蟲害", "皇帝豆常見蟲害；果莢較硬能抵抗許多蟲害，栽培相對容易", "有機防治：預防用矽藻土（破壞蟲體表皮蠟質層）、印楝素、苦楝油；治療用葵無露、夏油、礦物油、窄域油（覆蓋蟲體表面使其窒息）；可用黏蟲板監測粉蝨薊馬蚜蟲等數量", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9516", "official", "2026-08-19"),

    # 杭菊
    ("hangju", "白絹病", "病害", "病原菌Sclerotium rolfsii，主要危害莖基部，破壞維管束組織阻斷水分運輸，導致植株生長勢減弱並逐漸萎凋", "參考機能作物主題館防治方法", "農業知識入口網（機能作物主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=40408", "official", "2026-08-19"),
    ("hangju", "菊蚜等蟲害", "蟲害", "杭菊常見病蟲害包括薊馬、夜蛾、毒蛾、粉介殼蟲、葉蟎、介殼蟲及菊蚜等；主要病害另有黑斑病及炭疽病", "非農藥防治：蘇力菌防治夜蛾毒蛾幼蟲；性費洛蒙陷阱誘捕夜盜蟲；印楝油或礦物油防治粉介殼蟲薊馬蚜蟲葉蟎；黃色或藍色黏紙誘捕薊馬粉介殼蟲", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/subject/subject.php?id=20004", "qa", "2026-08-19"),

    # 紅蔥頭（分蔥，與蔥同屬，病原菌相同）
    ("hongcongtou", "紫斑病", "病害", "被害葉初呈淡褐色小型病斑，漸擴大成紡錘形，後凹陷為暗紫色紡錘形病斑，邊緣淡紅色至淡紫色，上下兩邊黃化，病斑上產生黑色黴狀物同心輪；此病原菌亦可危害同屬的蔥與大蒜", "參考植物保護手冊防治方法", "農業知識入口網", "https://kmweb.moa.gov.tw/knowledge_view.php?id=7320", "official", "2026-08-19"),

    # 青江菜
    ("qingjiangcai", "蚜蟲", "蟲害", "青江菜整年栽種除嚴冬外皆需注意蚜蟲侵害，刺吸葉液，被害嚴重時葉片捲縮或萎凋，植株生長不良", "酒精稀釋液100～400倍防治蚜蟲、粉介殼蟲；採收完畢立即整地割除殘株雜草消滅蟲源；黃色黏板誘殺成蟲", "農業知識入口網（種植教學整理）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=2374", "qa", "2026-08-19"),

    # 過貓（過溝菜蕨）
    ("guomao", "病蟲害極少", "其他", "過貓天然病蟲害極少，是少數不需噴灑農藥即可栽培的蔬菜之一，此特性也是其被視為友善環境作物的主要原因", "無須農藥防治", "農業知識入口網（原住民族農產業主題館）", "https://kmweb.moa.gov.tw/knowledge_view.php?id=9338", "official", "2026-08-19"),

    # 甜菜根
    ("tiancaigen", "甜菜夜蛾", "蟲害", "普遍發生於多種蔬菜與花卉之重要害蟲，成蟲晝伏夜出，一年可發生十餘代；初齡幼蟲取食葉背葉肉殘留上表皮，2～3齡後分散蠶食葉片呈不規則缺刻或孔洞，嫩芽花器亦可能受害",
     "可用陶斯松、第滅寧、汰芬諾克、馬拉松、芬化利、納乃得、畢芬寧、蘇力菌等藥劑防治",
     "農業知識入口網（甘藍主題館）", "https://kmweb.moa.gov.tw/subject/subject.php?id=13450", "official", "2026-08-19"),
]

UNVERIFIED = [
    ("xiaobaicai", "病毒病、軟腐病、霜霉病、黑斑病、蚜蟲、白粉虱、煙粉虱、菜青蟲、甜菜夜蛾等在多篇二手資料中被提及，但尚未從官方單一頁面取得防治細節，需另行查證。"),
    ("digualve", "適合季節、溫度範圍、土壤類型、株距、施肥方式尚未找到官方明確數據，目前僅有使用者問答等級的種植敘述，需另找改良場或農業部正式頁面補齊。"),
    ("digualve", "甘藷病毒病可造成產量90%以上損失，防治方式僅查到「種植去病毒健康種苗」，缺乏地瓜葉專屬（食用葉部而非塊根）的病蟲害資料，需另行查證。"),
    ("fanqie", "番茄病害（早疫病、晚疫病、青枯病、黃化捲葉病毒病等）僅查到病害名稱列表，尚未取得症狀與防治方法的官方原文，需點擊各篇原文逐一查證後才能收錄。"),
    ("fanqie", "水分管理、施肥劑量、採收天數尚未取得官方明確數據，原文僅提及「參照農業部施肥手冊及植物保護手冊」，需另行查找該手冊內容。"),
    ("kongxincai", "溫度範圍、土壤成分、株距尚未取得官方明確數據，原文僅強調耐熱耐濕、全年可栽培，需另找具體數據來源。"),
    ("kongxincai", "白鏽病在多篇資料中被列為空心菜常見病害，但本次查證的頁面實際診斷案例為葉蟎（紅蜘蛛），並非白鏽病，兩者症狀易混淆，白鏽病防治細節需另行查證。"),
    ("luobo", "本筆栽培資料原文使用「畝」「釐米」等中國大陸慣用單位與前作輪作建議，疑似轉載自中國農業網站內容，套用到台灣種植前，建議換算單位並與台灣農改場資料交叉核對，故全數標記為qa等級。"),
    ("luobo", "尚未取得台灣北中南分區栽培差異資料，僅知盛產期為12月至翌年初春，地區差異待補查。"),
    ("gaolicai", "施肥方案（用量、肥料種類）與病蟲害防治細節（除黑腐病外，小菜蛾、黃條葉蚤等常見蟲害的具體防治方式）尚未從官方頁面取得，需另行查證。"),
    ("dabaicai", "本筆資料多來自使用者問答，施肥數據使用「畝」單位（中國大陸慣用），套用到台灣前需換算並與台灣農改場資料交叉核對；適合季節、溫度、土壤、株距、採收天數等基本欄位仍缺，需找台灣官方栽培曆補齊。"),
    ("huaqielan", "土壤pH值、株距等具體栽培數據尚未取得；小菜蛾等蟲害雖在花椰菜主題館中列出，但本次僅查證到黑斑病的完整防治細節，蟲害部分需另行查證。"),
    ("xiaohuanggua", "露菌病、疫病、萎凋病、炭疽病、瓜實蠅、銀葉粉蝨等在多篇資料中被列為小黃瓜常見病蟲害，但本次僅查證到白粉病的完整防治細節，其餘需另行查證；株距數據亦尚未取得。"),
    ("malingshu", "官方主題館頁面提及晚疫病、瘡痂病、細菌性軟腐病、病毒病為主要病蟲害問題，但本次未查證到具體症狀與防治方法的原文，需另行查證；種薯繁殖與間隔資料僅來自使用者問答，需與官方資料交叉核對。"),
    ("huluobo", "黑斑病、黑腐病、根結線蟲病、軟腐病、胡蘿蔔花葉病等在搜尋結果中被列為常見病蟲害名稱，但本次未查證到症狀與防治方法的官方原文，需另行查證；施肥資料亦尚未取得；季節月份為「秋季/春天」的估算值，非原文精確月份。"),
    ("qiezi", "茄子主題館列出10種病害、7種蟲害，本次僅收錄最常見的青枯病、白粉病、二點小綠葉蟬、紅蜘蛛類4項，幼苗立枯病、炭疽病、疫病、根瘤線蟲、薊馬、粉蝨、斑潛蠅、多種蛾類等尚未收錄，需視需求後續補齊；適合播種季節亦尚未取得明確資料。"),
    ("tianjiao", "斑葉蟎、薊馬、粉蝨等蟲害在搜尋結果中被提及具體藥劑，但本次未透過WebFetch查證原文，暫不收錄，避免引用未直接核實的用藥劑量；分區播種月份（例如夏季高冷地、冬季恆春半島）也需另行查證。"),
    ("yangcong", "黃萎病、灰黴病亦是洋蔥常見病害，本次已查得症狀但因與軟腐病、紫斑病相比防治細節較簡略，暫未列入正式資料表；株距、施肥、採收天數等基本欄位仍缺，需另行查證。"),
    ("sigua", "白粉病是絲瓜另一常見病害（防治方法包含田區衛生管理、輪流用藥），黑守瓜為常見蟲害（可於苗期覆蓋紗網防治），本次因未透過WebFetch查證到完整原文防治細節，暫未收錄，需另行查證。"),
    ("sijidou", "銹病、白粉病、灰黴病、葉蟎、潛葉蠅等在搜尋結果中被列為四季豆常見病蟲害，但本次未查證到症狀與防治方法的官方原文，需另行查證；適合季節、溫度、土壤等基本欄位亦缺。"),
    ("bale", "立枯病、藻斑病、煤煙病、莖潰瘍病、枝枯病、粉介殼蟲、線蟲病害、腹鉤薊馬、黑疣粉蝨、捲葉蛾等在芭樂主題館中均有專頁，本次僅查證東方果實蠅一項，其餘需視需求後續補齊；定植季節的月份是排除典型雨季/颱風季後的推算值，非原文直接給出的月份，需另行查證核實。"),
    ("bocai", "本筆資料來自通俗種植教學（使用者問答等級），適合溫度、株距、明確採收天數等欄位缺失，需另尋台灣官方栽培曆（如農業改良場）補齊並交叉核對。"),
    ("jielan", "本筆資料來自通俗種植教學，內容偏向一般性園藝建議（非明確標示台灣在地技術資料），黑腐病、菜青蟲等病蟲害細節也僅有簡略描述，需另尋台灣官方芥藍栽培資料（如十字花科相關主題館）補齊並交叉核對。"),
    ("donggua", "適合季節、溫度、土壤、株距、水分管理、採收天數等基本欄位均缺，本次僅查得摘心整枝與施肥細節；病蟲害資料（露菌病、疫病、蚜蟲等常見問題）本次未查證到官方原文，需另行查證。"),
    ("nangua", "南瓜主題館雖有官方分區季節資料，但採收天數、株距、施肥等仍缺，本次以使用者問答補充部分資訊（已標記qa）；病蟲害僅查得果實蠅與潛葉蟲兩項使用者問答內容，白粉病、露菌病等常見病害尚未查證。"),
    ("kugua", "官方苦瓜主題館資料完整度高，但本次未收錄「苦瓜育苗技術與苗期管理」（發芽溫度30～35℃已知，其餘苗期細節未查證）及萎凋病以外的症狀描述，需視需求後續補齊。"),
    ("azhai", "溫度、土壤、水分管理、施肥等基本欄位尚未取得；病蟲害資料亦尚未查證，需另行補齊。"),
    ("yutou", "適合季節資料品質偏通俗教學（qa等級），溫度、土壤、株距、施肥等欄位均缺，需另尋官方芋頭栽培曆補齊並交叉核對；病蟲害資料則已有官方主題館的完整4項。"),
    ("jiang", "資料來源頁面（knowledge_view id=4362）內容雖詳實具體，但無法確認是否為官方發布或轉載自其他來源，建議之後與苗栗、花蓮等主要薑產區的農業改良場資料交叉核對；青枯病與軟腐病已補上症狀說明，但白絹病、根瘤線蟲、疫病仍僅有病名，防治方法多僅提及「參考植物保護手冊」缺乏具體藥劑，需另行補齊。"),
    ("wandou", "「平地」與「高冷地」栽培期未明確對應台灣哪些縣市/地區，暫套用平地期作為北中南通用值，需另行查證高冷地栽培的實際地理範圍；病蟲害資料尚未查證。"),
    ("maodou", "本次僅查得全國產期與主要產地，播種月份、株距、溫度、施肥等栽培細節與病蟲害資料均尚未查證，需另行補齊。"),
    ("ganju", "本次查得各柑橘品種的產期與傳統主產地，但溫度、土壤、栽培管理、病蟲害等細節尚未查證；「地區」為品種主產地而非播種季節，與蔬菜類的「現在適合種」邏輯不同，需在UI呈現時特別區分，避免使用者誤解為可播種月份。"),
    ("mangguo", "苗木定植適期(3～10月)已透過WebFetch核實官方頁面，炭疽病病蟲害資料亦已補齊；適合溫度、土壤（除定植方式外）、株距等資料，以及薊馬、介殼蟲、東方果實蠅等其餘蟲害資料仍尚未查證。"),
    ("mugua", "定植適期(春植2～3月/秋植9～11月)已透過WebFetch核實食農教育資訊整合平臺頁面；適合溫度、病蟲害資料仍尚未查證。"),
    ("fengli", "溫度、土壤、株距（僅有種植密度）、病蟲害等資料均尚未查證；種植時間需依目標採收月份與芽種類反推計算，不適合簡化成單一月份範圍，需另行設計更複雜的判斷邏輯。"),
    ("lianwu", "適合溫度、株距為既有果樹的栽培參數，土壤、施肥細節已有基本資料，但病蟲害資料尚未查證；「苗木定植季節」與蔬菜播種季節的意義不同，需在UI呈現時說明清楚。"),
    ("yumi", "僅查得南部播種期，北部、中部播種期尚未查證；土壤、水分管理、施肥、病蟲害等資料均尚未查證。"),
    ("digua", "本次資料聚焦於插植適期與株距，土壤條件、施肥、病蟲害等細節尚未查證（可參考同屬甘藷科的地瓜葉病蟲害資料，如甘藷蟻象、甘藷猿葉蟲、甘藷簇葉病，但需確認是否適用於採收塊根的地瓜栽培情境）。"),
    ("xiangjiao", "適合種植季節多次查證仍未找到官方明確月份（僅查到「產期」依吸芽發生月份分春蕉3-5月/夏蕉6-9月/秋冬蕉10月至翌年2月採收，但這是採收期非種植期），season欄位誠實留空；溫度、土壤等基本欄位亦缺；病蟲害資料（嵌紋病、萎縮病、黃葉病、球莖象鼻蟲、假莖象鼻蟲、花薊馬等）本次僅查得名稱列表，未查證症狀與防治方法原文，需另行補齊。"),
    ("lvhuaqielan", "本次查詢多次仍未取得青花菜專屬的官方栽培資料，查到的頁面實際為花椰菜（白花）內容，已明確標記警示不作為青花菜正式數據；建議下次直接搜尋「綠花椰菜」或指定青花菜主題館頁面ID查證。"),
    ("jiucai", "溫度以外的土壤、株距、水分管理、施肥細節（除花蓮區合理化施肥概述）尚未完整查證；薊馬與白絹病已補上症狀與防治方法，銹病等其餘病蟲害仍待補齊。"),
    ("cong", "紫斑病已補上症狀與病原菌說明，但防治方法僅提及「參考植保手冊」缺乏具體藥劑；菌核病、赤銹病、甜菜夜蛾、潛蠅等其餘病蟲害本次僅查得名稱列表，需另行補齊。"),
    ("dasuan", "病蟲害資料（萎黃病、細菌性軟腐病、蔥潛蠅等）本次僅查得名稱列表，未查證症狀與防治方法原文，需另行補齊。"),
    ("xigua", "銀葉粉蝨病蟲害資料已補齊；土壤、種植方式、株距、施肥等栽培細節，以及蔓枯病等其餘病蟲害仍尚未查證；北部、中部分區資料亦缺，需另行補齊。"),
    ("jiecai", "株距、採收天數尚未取得；病蟲害資料（嵌紋病毒、軟腐病、黑腐病、根瘤病、露菌病、蚜蟲類、斜紋夜蛾、紋白蝶、小菜蛾、黃條葉蚤）本次僅查得名稱列表，未查證症狀與防治方法原文，需另行補齊。"),
    ("youcai", "季節資料僅以台東地區為例，全台適用性未查證；土壤、種植方式、株距、採收天數、病蟲害等資料均缺，需另行補齊。油菜常作為綠肥/景觀作物而非食用蔬菜栽培，用途定位需在UI呈現時說明清楚。"),
    ("lizhi", "適合溫度、土壤條件（除定植植穴處理）等基本欄位尚未取得；病蟲害資料（荔枝椿象、荔枝細蛾、炭疽病等常見問題）本次未查證，需另行補齊。"),
    ("longyan", "適合溫度、土壤條件、株距等新植栽培資料尚未取得；病蟲害資料（荔枝椿象、木蝨、炭疽病等）本次未查證，需另行補齊。"),
    ("baixiangguo", "適合溫度、土壤條件、株距等資料尚未取得；病蟲害資料（褐色圓斑病、木質化病毒病、東方果實蠅等）本次未查證，需另行補齊。"),
    ("huolongguo", "扦插/種植的確切適合季節本次未能以WebFetch查證單一官方來源，season欄位暫留空，之後應直接搜尋台灣農業改良場（如台南區、高雄區）的紅龍果專頁補齊；株距、施肥週期、病蟲害資料亦尚未完整查證。"),
    ("shanyao", "施肥資料與北部以外地區的病蟲害資料尚未查證；中南部分區種植資料亦缺，需另行補齊。"),
    ("niupang", "本筆資料來自通俗種植教學（qa等級），非直接來自台灣官方牛蒡主題館，株距、施肥、水分管理、病蟲害等資料均缺，需另行查證並替換為官方來源。"),
    ("lusun", "土壤條件、水分管理、施肥等基本欄位尚未取得；病蟲害資料（蘆筍莖枯病、蘆筍夜蛾等）本次未查證症狀與防治方法原文，需另行補齊。"),
    ("jiaobaisun", "分株定植的確切月份原文未提供，season欄位暫留空；施肥、病蟲害資料（黑穗病等）本次未完整查證，需另行補齊。"),
    ("hongdou", "適合溫度、土壤、株距、施肥等基本欄位尚未取得；病蟲害資料本次未查證，需另行補齊；北部、中部是否適合栽培及原因尚待查證（官方資料僅強調南部秋作為主）。"),
    ("huasheng", "播種月份是根據「農曆採收期＋成長期4個月」反推估算，並非原文直接給出的播種月份，需另行查證官方播種曆核實；銹病與白絹病病害資料已補齊，但土壤條件（除排水良好砂質壤土）、株距、施肥，以及紅蜘蛛、小綠葉蟬等蟲害資料仍尚未完整查證。"),
    ("putao", "本次資料聚焦於既有植株的產期調節模式，新植苗木的種植月份、適合溫度、土壤、株距等基本欄位尚未取得；病蟲害資料（露菌病、黑痘病、金龜子等）本次未查證，需另行補齊。"),
    ("caomei", "產地分布（大湖、內湖等主要產區）本次未查得官方原文佐證；病蟲害資料（灰黴病、白粉病、紅蜘蛛等）本次未查證，需另行補齊。"),
    ("qiukui", "北中南分區月份是根據搜尋摘要整理而非單一WebFetch核實頁面，需另行以官方分區栽培曆核對；病蟲害資料（二點小綠葉蟬、棉蚜、南黃薊馬、潛蠅、白粉病、病毒病）本次僅查得名稱列表，未查證症狀與防治方法原文。"),
    ("huanggongcai", "整體資料品質偏通俗種植教學（qa等級），適合溫度、土壤、株距等基本欄位缺，需另尋官方落葵/保健植物主題館資料補齊並交叉核對；病蟲害資料未查證（原文提及對病蟲害抵抗力強，栽培期間可不用農藥，但缺乏具體病蟲害清單）。"),
    ("jiucengta", "整體資料品質偏通俗種植教學（qa等級），土壤pH、株距、施肥等基本欄位缺，需另尋官方羅勒/香草植物主題館資料補齊；病蟲害資料未查證。"),
    ("xiangcai", "整體資料品質偏通俗種植教學（qa等級），土壤條件、株距、施肥等基本欄位缺，需另尋官方芫荽栽培資料補齊；病蟲害資料未查證。"),
    ("lianou", "水分管理（除萌芽生長溫度外）、施肥等細節尚未取得；病蟲害資料本次未查證，需另行補齊。"),
    ("yangtao", "定植適期的確切月份原文未給出，season欄位暫留空；土壤條件、株距、水分管理、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("shijia", "水分管理、施肥等栽培細節尚未取得；病蟲害資料（介殼蟲、椿象、炭疽病等）本次未查證，需另行補齊。"),
    ("tianshi", "定植適期的確切月份原文未給出，season欄位暫留空；土壤條件、株距、水分管理、施肥、病蟲害等資料均缺，需另行補齊；甜柿為高冷地果樹，「現在適合種」邏輯需額外考慮海拔限制，與平地作物不同。"),
    ("yangxiangua", "宜蘭端午節前後產期的細節來自搜尋摘要整理未經WebFetch逐一核實；適合溫度、土壤、種植方式、株距等栽培細節與病蟲害資料均缺，需另行補齊。"),
    ("longxucai", "土壤、繁殖、採收等資料來自使用者問答（qa等級），適合溫度雖具體但同樣為qa來源，需另尋官方龍鬚菜/佛手瓜主題館資料補齊並交叉核對；病蟲害資料未查證。"),
    ("shansu", "北部、中部人工栽培資料尚未取得；適合溫度、土壤條件、株距、施肥等栽培細節與病蟲害資料均缺，需另行補齊。"),
    ("guomao", "適合溫度、土壤條件、株距、施肥等栽培細節與病蟲害資料均缺，需另行補齊。"),
    ("tiancaigen", "水分管理以外的施肥細節、株距、採收天數等尚未取得；病蟲害資料未查證，需另行補齊。"),
    ("biqi", "「春末」推估為4～5月，非原文直接給出的精確月份，需另行查證確切播種月份；株距、施肥等栽培細節與病蟲害資料均缺，需另行補齊。"),
    ("pingguo", "苗木定植的確切月份原文未給出，season欄位暫留空；蘋果為高冷地果樹（與甜柿類似），「現在適合種」邏輯需考慮海拔限制；病蟲害資料本次未查證。"),
    ("pipa", "生育週期資料來源標示不夠清楚是否為官方頁面（qa等級），需另尋官方枇杷主題館資料交叉核對；定植月份未給出，土壤條件、株距、水分管理等資料缺，病蟲害資料未查證。"),
    ("hongzao", "資料來源標示不夠清楚是否為官方頁面（qa等級），需另尋官方紅棗主題館資料交叉核對；定植月份、土壤條件、株距、水分管理、施肥等資料缺，病蟲害資料未查證。"),
    ("laoli", "適合溫度、土壤條件等基本欄位尚未取得；病蟲害資料（炭疽病、根腐病、薊馬等）本次未查證，需另行補齊。"),
    ("dadou", "土壤條件、株距、施肥等栽培細節尚未取得；北中南分區資料亦缺；病蟲害資料（銹病、露菌病、豆莢螟等）本次未查證，需另行補齊。"),
    ("jinzhen", "中部、南部分區資料尚未取得（僅查得本地種對北部/東部海拔的要求）；水分管理、施肥細節、病蟲害資料本次未查證，需另行補齊。"),
    ("xiancao", "北中南分區資料尚未取得；水分管理細節、病蟲害資料本次未查證，需另行補齊；season欄位採用「移植本田」的2～3月，但8月的扦插育苗期同樣是重要的準備時機，需在UI呈現時考慮是否也要標示。"),
    ("luoshenkui", "北部分區資料尚未取得；適合溫度、水分管理、病蟲害資料本次未查證，需另行補齊。"),
    ("kafei", "官方咖啡主題館資料完整度高（定植適期已核實），但病蟲害資料未查證（搜尋摘要提及「幾乎沒有病蟲害」但缺乏具體原文佐證）；土壤條件、水分管理細節亦缺。"),
    ("lingjiao", "適合種植季節的確切月份本次未能核實單一官方來源，season欄位暫留空；土壤、水分管理、株距、施肥、病蟲害等資料均缺，需另行以官方原文補齊。"),
    ("yelian", "整體資料品質偏搜尋摘要整理（qa等級），需另尋高雄區農業改良場等官方原文核實；適合溫度、水質要求、施肥、病蟲害等基本欄位缺。"),
    ("shudou", "播種月份原文未給出，season欄位暫留空；土壤條件、株距、水分管理、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("taiwanli", "播種月份原文未給出，season欄位暫留空；適合溫度、土壤條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("xiaomi", "季節月份為春秋作的推估值（春作約2～4月、秋作約8～10月），非原文直接給出的精確月份；株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("ningmeng", "定植適期原文未能核實，season欄位暫留空；株距、水分管理、病蟲害等資料未查證，需另行補齊；與柑橘(ganju)為近緣作物，可考慮之後統一在同一分類下比較資料。"),
    ("hongcongtou", "整體資料來源為搜尋摘要整理（qa等級），未逐一以WebFetch核實單一官方頁面；株距、施肥、病蟲害等資料均缺，需另行查證並替換為官方來源。"),
    ("lajiao", "北中南分區資料本次未查證到官方原文（早期搜尋摘要曾提及分區月份但未經WebFetch核實，故未採用）；株距、施肥細節與病蟲害資料（炭疽病、疫病、薊馬、蚜蟲等）均缺，需另行補齊。"),
    ("qingjiangcai", "土壤條件、適合溫度、株距等基本欄位尚未取得明確數據；病蟲害資料僅提及「注意蚜蟲侵害」，缺乏完整防治方法，需另行補齊。"),
    ("qincai", "溫度、土壤、株距、施肥、水分管理、病蟲害等具體栽培細節均缺，本次僅查得季節與品種概述，需另行查證官方栽培技術頁面補齊。"),
    ("bianbu", "適合播種季節的確切月份原文未給出，season欄位暫留空；土壤條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("hugua", "北部、中部分區資料尚未取得；土壤條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("jianghuang", "水分管理細節、病蟲害資料本次未查證，需另行補齊；薑黃與薑(jiang)為近緣作物，可考慮之後統一比較栽培資料。"),
    ("lanmei", "定植適期的確切月份原文未給出，season欄位暫留空；土壤pH需求明確(<5.2)但完整土壤配方、株距、施肥週期、病蟲害等資料均缺，需另行補齊。"),
    ("huangdidou", "最適播種月份原文未直接給出（僅知7～8月種植需額外防護），season欄位暫留空，需另行查證官方萊豆栽培曆核實正確播種月份；株距、施肥、病蟲害等資料均缺。"),
    ("qiujingganlan", "播種月份原文未給出，season欄位暫留空；適合溫度、土壤條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("yuegua", "整體資料來源為搜尋摘要整理（qa等級），未以WebFetch核實單一官方頁面；適合溫度、土壤、株距、施肥、病蟲害等資料均缺，需另行查證並替換為官方來源。"),
    ("jiangdou", "播種月份原文未給出，season欄位暫留空；適合溫度、土壤條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("midou", "播種月份原文未給出，season欄位暫留空；土壤條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("ganzhe", "適合溫度、土壤詳細條件、株距、施肥、病蟲害等資料均缺，需另行補齊。"),
    ("huma", "播種月份為依生育期(80～90天)反推的估算值，非原文直接給出的精確月份，需另行查證核實；適合溫度、土壤條件、株距、施肥、病蟲害等資料均缺。"),
    ("hangju", "種植月份(4月清明後至7月前)來自搜尋摘要整理，未經WebFetch單一官方頁面直接核實，標記為qa；施肥、病蟲害等資料均缺，需另行補齊。"),
]


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        DROP TABLE IF EXISTS cultivation_facts;
        DROP TABLE IF EXISTS pests;
        DROP TABLE IF EXISTS unverified_notes;
        DROP TABLE IF EXISTS crops;
        DROP TABLE IF EXISTS crop_registry;
    """)
    conn.executescript(SCHEMA)

    conn.executemany(
        "INSERT INTO crop_registry (crop_id, name, category, status) VALUES (?, ?, ?, ?)",
        REGISTRY,
    )
    conn.executemany(
        "INSERT INTO crops (crop_id, name, category, region_north, region_central, region_south, region_note, "
        "season_months_north, season_months_central, season_months_south, season_label) "
        "VALUES (:crop_id, :name, :category, :region_north, :region_central, :region_south, :region_note, "
        ":season_months_north, :season_months_central, :season_months_south, :season_label)",
        CROPS,
    )
    conn.executemany(
        "INSERT INTO cultivation_facts (crop_id, field, value, source_name, source_url, source_type, fetched_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        CULTIVATION,
    )
    conn.executemany(
        "INSERT INTO pests (crop_id, name, type, symptom, control, source_name, source_url, source_type, fetched_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PESTS,
    )
    conn.executemany(
        "INSERT INTO unverified_notes (crop_id, note) VALUES (?, ?)",
        UNVERIFIED,
    )
    conn.commit()

    counts = {
        "crop_registry": conn.execute("SELECT COUNT(*) FROM crop_registry").fetchone()[0],
        "crops": conn.execute("SELECT COUNT(*) FROM crops").fetchone()[0],
        "cultivation_facts": conn.execute("SELECT COUNT(*) FROM cultivation_facts").fetchone()[0],
        "pests": conn.execute("SELECT COUNT(*) FROM pests").fetchone()[0],
        "unverified_notes": conn.execute("SELECT COUNT(*) FROM unverified_notes").fetchone()[0],
    }
    conn.close()
    print(f"Built {DB_PATH}")
    print(counts)


if __name__ == "__main__":
    main()
