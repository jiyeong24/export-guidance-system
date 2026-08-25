import os
import streamlit as st
from dotenv import load_dotenv
import oracledb
import pandas as pd
import requests
import xml.etree.ElementTree as ET

load_dotenv()
COUNTRY_ITEM_KEY=os.getenv("COUNTRY_ITEM_KEY")
COUNTRY_KEY=os.getenv("COUNTRY_API_KEY")
TARIFF_KEY=os.getenv("TARIFF_KEY") #환율 가져오기
TARIFF_RATE_KEY=os.getenv("TARIFF_RATE_KEY") #관세 가져오기

st.set_page_config(page_title="수출 정보 제공 시스템")

st.title("초보 사업자를 위한 수출 정보 제공 시스템 ")
st.write("상품 정보를 입력하면 수출에 필요한 정보를 분석해드립니다")

#국가별 관세율표 불러오기
tariff_files={
  "US":"tariff/2025년_미국_관세율표_rev32.xlsx",
  "CN":"tariff/2025년_중국_관세율표.xlsx",
  "VNM":"tariff/2025년_베트남_관세율표.xlsx",
  "TWN":"tariff/2025년_대만_관세율표.xlsx",
  "AUS":"tariff/2025년_호주_관세율표.xlsx",
  "CAN":"tariff/2025년_캐나다_관세율표.xlsx",
  "THA":"tariff/2025년_태국_관세율표.xlsx",
  "RUS":"tariff/2025년_러시아_관세율표.xlsx"
}




#<입력>
#총가격 계산을 위한 입력
st.header("상품 정보 입력")
product_name=st.text_input("상품명", placeholder="예:화장품")
importing_country=st.text_input("수입국", placeholder="예:US,AUS,CN")
price=st.number_input("판매가격",min_value=0.0, value=0.0)
quantity=st.number_input("판매수량",min_value=1, value=1)
hs_code=st.text_input("HS CODE",placeholder="아래 표에서 품목에 맞는 hs code를 찾아 입력해주세요")
start_month=st.text_input("start month",placeholder="예:202501")
finish_month=st.text_input("finish month",placeholder="예:202601")
hs_data=pd.read_excel("hs_data.xlsx",sheet_name="HS10단위", dtype=str)
st.write(hs_data)

#관세 계산을 위한 입력
search_date=st.text_input("환율정보를 알고싶은 날짜(연,월,일) : ",placeholder="예:20141226")

#API연결
def get_trade_data(service_key, hs_code,country_code, start_month, end_month):
  url = "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"
  params={
    "serviceKey": service_key,
    "strtYymm": start_month,
    "endYymm":end_month,
    "hsSgn" : hs_code,
    "cntyCd" : country_code
  }
  response = requests.get(url, params=params)
  root=ET.fromstring(response.text)

  result_code = root.findtext(".//resultCode")

  data=[]

  for item in root.findall(".//item"):
    data.append({
      "기간": item.findtext("year"),
      "국가": item.findtext("statCdCntnKor1"),
      "HS Code": item.findtext("hsCd"),
      "품목명": item.findtext("statKor"),
      "수출중량(kg)": item.findtext("expWgt"),
      "수출금액($)": item.findtext("expDlr"),
      "수입중량(kg)": item.findtext("impWgt"),
      "수입금액($)": item.findtext("impDlr"),
      "무역수지($)": item.findtext("balPayments")
      })
  return data



def cal_exchange(search_date, ex_or_im):
  url="https://unipass.customs.go.kr:38010/ext/rest/trifFxrtInfoQry/retrieveTrifFxrtInfo"
  params={
    "crkyCn": COUNTRY_ITEM_KEY,
    "qryYymmDd" :search_date, #조회년월일(예:20141228)
    "imexTp" : ex_or_im #수출입구분
  }
  response = requests.get(url, params=params)
  print(response.url)
  print(response.text)

  root=ET.fromstring(response.text)
  data = []

  for item in root.findall(".//trifFxrtInfoQryRsltVo"):
    data.append(
      {
        "국가코드":item.findtext("cntySgn"),
        "화폐":item.findtext("mtryUtlNm"),
        "환율":item.findtext("fxrt"),
        "통화코드":item.findtext("currSgn"),
        "적용일자":item.findtext("aplyBgnDt"),
        "수출입구분":item.findtext("imexTp")      }
    )
  return data

#관세정보
def get_tariff_rate(hs_code):
  url="https://unipass.customs.go.kr:38010/ext/rest/trrtQry/retrieveTrrt"
  params = {
    "crkyCn" : TARIFF_RATE_KEY,
    "hsSgn" : hs_code #hs부호   
  }

  response = requests.get(url, params=params)

  root = ET.fromstring(response.text)

  data= []

  for item in root.findall(".//TrrtQryRsltVo"):
    data.append({
            "HS CODE": item.findtext("hsSgn"),
            "관세율코드": item.findtext("trrtTpcd"),
            "관세율명": item.findtext("trrtTpNm"),
            "관세율": item.findtext("trrt"),
            "단위당세액": item.findtext("prutXamt"),
            "기준가격": item.findtext("basePrc"),
            "적용시작일": item.findtext("aplyStrtDt"),
            "적용종료일": item.findtext("aplyEndDt")
        })

  return data

#화면 출력
if st.button("수출 정보 분석") :
  if not product_name:
    st.warning("상품명을 입력하세요")
  elif not importing_country:
    st.warning("수입국을 입력하세요")
  elif not hs_code:
    st.warning("HS CODE를 입력하세요")
  else:
    #상품 가격 계산
    total_price=price*quantity
    st.subheader("상품정보")
    st.write(f"상품명 : {product_name}")
    st.write(f"수입국 : {importing_country}")
    st.write(f"판매 가격 : {price}")
    st.write(f"수량 : {quantity}")
    st.write(f"HS_CODE: {hs_code}")

    st.subheader("수출 정보")
    tariff_hs_code=hs_code
    trade_hs_code=hs_code[:4]

    #수출 총 계산을 하기 위함
    data=get_trade_data(COUNTRY_ITEM_KEY, trade_hs_code,importing_country, start_month, finish_month)

    if data:
       st.dataframe(data)
    else:
       st.write("조회된 데이터가 없습니다")

    st.metric(
      "상품 총 가격", f"{total_price:,.0f}원"
    )

    st.info("API를 이용한 상품 및 관세 정보를 조회합니다.")
    st.subheader("결과")
    total_weight = sum(float(item["수출중량(kg)"]or 0)for item in data)
    total_export = sum(float(item["수출금액($)"]or 0)for item in data)
    if total_weight >0:
      export_per_weight = total_export/total_weight
      st.write("총 수출중량 : ", total_weight)
      st.write("총 수출금액 : ", total_export)
      st.write("kg당 수출금액 : ", export_per_weight)
        
      if export_per_weight>100:
        st.subheader("수출하기 좋은 시기!")
      else:
        st.write("현재 수출금액/중량 기준으로 수출하기 좋은 시기가 아닙니다")
    else:
      st.write("데이터가 존재하지 않습니다")

    exchange_data=cal_exchange(search_date,"1") #1이 수출
    st.write("TARIFF_RATE_KEY 존재:", TARIFF_RATE_KEY is not None)
    st.write("COUNTRY_ITEM_KEY 존재:", COUNTRY_ITEM_KEY is not None)

    country_code=importing_country.upper()
    file=tariff_files[country_code]
    tariff_data=pd.read_excel(file,dtype=str)
    hs10 = str(tariff_hs_code).zfill(10)
    matched=tariff_data[
      tariff_data["세번"].str.strip()==hs10
    ]
    if matched.empty:
      st.warning(f"{country_code}관세율표에서 HS CODE를 찾을 수 없습니다.")
    else:
      tariff_rate=str(matched.iloc[0]["Rate of Duty 1 General\n기본세율"]).strip()
      tariff_rate=tariff_rate.replace("%","")

      st.write("HS CODE:",hs10)
      st.write("관세율:",tariff_rate)

      real_tr=float(tariff_rate)/100
      
      st.write("관세:",total_price*real_tr)


    
        


