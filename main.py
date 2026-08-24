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
ITEM_KEY=os.getenv("ITEM_API_KEY")

st.set_page_config(page_title="수출 정보 제공 시스템")

st.title("초보 사업자를 위한 수출 정보 제공 시스템 ")
st.write("상품 정보를 입력하면 수출에 필요한 정보를 분석해드립니다")

st.header("상품 정보 입력")
product_name=st.text_input("상품명", placeholder="예:화장품")
exporting_country=st.text_input("수출국", placeholder="예:대한민국")
importing_country=st.text_input("수입국", placeholder="예:US,JP,CN")
price=st.number_input("판매가격",min_value=0.0, value=0.0)
quantity=st.number_input("판매수량",min_value=1, value=1)
hs_code=st.text_input("HS CODE",placeholder="아래 표에서 품목에 맞는 hs code를 찾아 입력해주세요")
start_month=st.text_input("start month",placeholder="예:202501")
finish_month=st.text_input("finish month",placeholder="예:202601")

hs_data=pd.read_excel("hs_data.xlsx")
st.write(hs_data)

#conn=oracledb.connect(user="scott", password="tiger", dsn="localhost:1521/EMPPDB")
#cursor=conn.cursor()

#상품명
#sql="INSERT INTO product_info (product_name) VALUES (:1)"
#cursor.execute(sql,(product_name,))
#conn.commit()

#수출국
#sql="INSERT INTO exporting_country_info (country_name) VALUES (:1)"
#cursor.execute(sql,(Exporting_country,))
#conn.commit()

#수입국
#sql="INSERT INTO importing_country_info (country_name) VALUES (:1)"
#cursor.execute(sql,(Importing_country,))
#conn.commit()


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
   

if st.button("수출 정보 분석") :
  if not product_name:
    st.warning("상품명을 입력하세요")
  elif not exporting_country:
    st.warning("수출국을 입력하세요")
  elif not importing_country:
    st.warning("수입국을 입력하세요")
  elif not hs_code:
    st.warning("HS CODE를 입력하세요")
  else:
    #상품 가격 계산
    total_price=price*quantity
    st.subheader("상품정보")
    st.write(f"상품명 : {product_name}")
    st.write(f"수출국 : {exporting_country}")
    st.write(f"수입국 : {importing_country}")
    st.write(f"판매 가격 : {price}")
    st.write(f"수량 : {quantity}")
    st.write(f"HS_CODE: {hs_code}")

    st.subheader("수출 정보")

    data=get_trade_data(COUNTRY_ITEM_KEY, hs_code,importing_country, start_month, finish_month)

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
      st.write("총 수출금액 : ", total_weight)
      st.write("kg당 수출금액 : ", export_per_weight)
        
      if export_per_weight>100:
        st.subheader("수출하기 좋은 시기!")
      else:
        st.write("현재 수출금액/중량 기준으로 수출하기 좋은 시기가 아닙니다")
    else:
      st.write("데이터가 존재하지 않습니다")
        


