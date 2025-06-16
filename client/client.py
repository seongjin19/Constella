import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from skyfield.api import (
    load, wgs84, Star,
    load_constellation_map, load_constellation_names
)
from PIL import Image, ImageDraw
import requests
import io

st.set_page_config(page_title="Constella", layout="centered")
# 이미지 파일 읽기
with open("title_baner.png", "rb") as f:
    img_data = f.read()

# base64로 인코딩
import base64
img_base64 = base64.b64encode(img_data).decode()

# HTML 마크업으로 배너 이미지 + 가운데 텍스트 삽입
st.markdown(f"""
<div style="position:relative; text-align:center; width:100%;">
  <img src="data:image/png;base64,{img_base64}" style="width:100%; border-radius:10px;" />

  <div style="
      position:absolute;
      top:50%;
      left:50%;
      transform:translate(-50%, -50%);
      color:white;
      text-shadow:2px 2px 8px black;
  ">
    <h1 style="font-size:48px; margin: 0;">Constella</h1>
    <h2 style="font-size:24px; margin: 0;">현재 위치에서 보이는 별자리 탐지</h2>
  </div>
</div>
""", unsafe_allow_html=True)



# ① 위치 받아오기
location = streamlit_geolocation()

# ② 유효성 검사
if not location or location.get("latitude") is None or location.get("longitude") is None:
    st.info("위치 정보를 아직 가져오지 못했습니다.\n브라우저에서 위치 사용을 허용해주세요.")
    st.stop()

# ③ 위도/경도 출력
lat = location["latitude"]
lon = location["longitude"]

# 역지오코딩
@st.cache_data
def reverse_geocode(latitude, longitude):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"format": "jsonv2", "lat": latitude, "lon": longitude}
    headers = {"User-Agent": "ConstellaApp"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("display_name", "")
    except Exception:
        return f"({latitude:.4f}, {longitude:.4f})"

place_name = reverse_geocode(lat, lon)
st.write(f"**위치:** {place_name}")

# ④ Skyfield 설정
ts    = load.timescale()
t     = ts.now()
eph   = load("de421.bsp")
earth = eph["earth"]
topos = wgs84.latlon(lat, lon)
observer = (earth + topos).at(t)

# ⑤ 별자리 경계 및 이름 맵
constellation_at = load_constellation_map()
names_map        = dict(load_constellation_names())

# ⑥ 지평선 위 보이는 별자리 계산
visible = set()
for ra_h in range(24):
    for dec_deg in range(-90, 91, 10):
        star = Star(ra_hours=ra_h, dec_degrees=dec_deg)
        astrometric = observer.observe(star).apparent()
        alt, _, _ = astrometric.altaz()
        if alt.degrees > 0:
            abbr = constellation_at(astrometric)
            visible.add(abbr)

# ⑦ 관심 별자리 필터
interest_full = [
    'Aquila','Bootes','Cassiopeia',
    'Cygnus','Gemini','Leo','Orion',
    'Scorpius','Taurus','Ursa Major'
]
filtered = [
    names_map[abbr] for abbr in visible
    if names_map.get(abbr) in interest_full
]

# ⑧ 서버 전송용 클래스명 변환
classes_to_send = [name.lower().replace(' ', '_') for name in filtered]

# ⑨ 필터링 결과 출력
if filtered:
    st.subheader("관측 가능한 별자리")

    # 별자릴 설명
    constellation_info = {
        'Aquila':
            {
                'image' : "image/aquila.png",
                'description': '독수리자리 \n'
                               '\n'
                               '그리스 신화에서 독수리는 가니메데를 납치하기 위하여 제우스가 변한 모습이라고 전해지고 있다. '
                               '청춘의 여신 헤베가 신들을 위해 술을 따르는 일을 하지 못하게 되자 제우스는 그녀의 일을 대신할 아름다운 젊은이를 찾기 위해 독수리로 변해 지상으로 내려갔다. '
                               '제우스는 이다산에서 트로이의 양떼를 돌보고 있던 아름다운 왕자 가니메데를 발견하고 그를 납치해 간다. '
                               '그 후 가니메데는 올림푸스 산에서 신들을 위해 술을 따르는 일을 하게 되었다.  \n'
                               '\n'
                               '하늘의 독수리자리는 변신한 제우스의 모습인 것이다. 우리나라에서도 칠월 칠석의 전설이 내려오고 있다.(원래는 중국의 전설이다) '
                               '아버지인 천제의 명령으로 옷감을 짜고 있던 직녀라는 공주는 은하수 서쪽에 살고 있었다. '
                               '그런데 강 건너에 사는 소치는 견우와 서로 사랑하게 되어 결혼하였다. '
                               '그러나 결혼한 뒤 그들은 자신의 일들은 뒤로 한 채 둘만의 시간을 보냈다. '
                               '몇 번의 주의를 주었으나 그들이 계속 일을 게을리 하였고, 천제는 매우 화가 났다. '
                               '그리하여 직녀와 견우를 불러 은하수의 양쪽에 갈라놓고, 1년에 한번만 만나도록 허락해 주었다.'
                               ' 그날이 바로 음력 7월7일이다. 그러나 은하수때문에 서로 만날 수 없어 그들이 흘리는 눈물로 지상에 비가 내렸다. '
                               '이를 불쌍히 여긴 까치들이 다리를 놓아 서로 만날 수 있게 되었고, 더 이상 그들은 눈물을 흘리지 않게 되었다.'
            },
        'Bootes':
            {
                'image' : "image/bootes.png",
                'description': '목동자리\n'
                               '\n'
                               '국자모양 북두칠성의 손잡이를 따라 커다란 곡선을 이어가다보면 밝고 오렌지색을 띠는 밝은 별이 있다.'
                               '이 별이 목동자리의 으뜸별인 아크투루스로, 동양의 별자리에서는 대각성(大角星)이다. '
                               '목동자리는 마름모꼴을 하고있는데, 아크투루스를 허리 위치로 보고 이를 기준으로 머리와 양 어깨에 해당하는 별들로 이루어져있다. \n'
                               '\n'
                               '또 다른 설은 어깨에 하늘을 짊어지고 돌이 된 거인 아틀라스라고도 한다. '
                               '아틀라스는 우주에 처음 나타난 하늘의 신 우라노스의 아들인데, 크로노스(제우스의 아버지)의 형제라고도 하고, '
                               '또는 우라노스의 손자로서 크로노스의 조카라고도 한다. \n'
                               '\n'
                               '제우스가 올림포스의 신들을 거느리고 거인 족과 싸웠을 때 '
                               '아틀라스는 거인 족을 지휘하여 제우스를 크게 괴롭혔다. '
                               '그래서 그 형벌로 영원히 하늘을 짊어질 운명이 되었다고 한다.'
            },
        'Cassiopeia': {
                'image' : "image/cassiopeia.png",
                'description': '카시오페아자리\n'
                               '\n'
                               '북쪽 하늘의 별자리로, W자의 형태를 하고 있다. '
                               '북반구 중위도 이상에서는 대부분의 밤하늘에 항상 떠 있고 북두칠성과 거의 마주보고 있어 쉽게 찾을 수 있다. \n'
                               '\n'
                               '북극성을 찾는 데에 이용되는데, 양쪽 두 변을 연결하여 만나는 지점과 가운데 별을 이어 5배만큼 나아가면 북극성을 찾을 수 있다. '
                               '그리스 신화에서 카시오페이아는 에티오피아의 왕비이다. 자랑을 좋아하여, '
                               '딸 안드로메다와 바다의 요정과 아름다움을 비교한 일로 바다의 신 포세이돈이 노하여 나라에 큰 재해를 일으켰다.'
                               '신탁에서 안드로메다를 괴물 고래에 산 제물로 바치면 포세이돈의 노여움이 풀릴 것이라고 하였고, '
                               '어쩔 수 없이 안드로메다를 해안에 사슬로 묶어 놓았는데, 페르세우스가 구해준다. '
                               '\n'
                               '카시오페이아는 하늘에 올려져 별자리가 되었지만, 포세이돈이 그녀가 바다에 내려와 쉬는 것을 허락하지 않았고, '
                               '그래서 항상 하늘 위에서 계속 돌고 있다고도 한다. '

            },
        'Cygnus': {
                'image' : "image/cygnus.png",
                'description': '백조자리\n'
                               '\n'
                               '백조자리는 독수리자리와 마찬가지로 제우스가 변신한 모습이다. '
                               '제우스는 스파르타의 왕비 레다의 아름다움에 빠져 그녀를 유혹하게 되었다. '
                               '하지만 질투가 심한 아내 헤라에게 들킬 것을 염려한 제우스는 그녀를 만나러 갈 때면 백조로 탈바꿈하여 올림푸스 산을 빠져 나오곤 했다.'
                               '\n'
                               '제우스의 사랑을 받아들인 레다는 두 개의 알을 낳게 되는데 그중 하나에서는 카스트로란 남자아이와 크리타이메스타라는 여자아이가 나왔고, '
                               '다른 하나에서는 폴룩스라는 남자아이와 헬렌이라는 여자아이가 태어났다. 이들이 자라서 카스트로와 폴룩스는 로마를 지켜주는 위대한 영웅이 되었고, '
                               '헬렌은 절세의 미인으로 트로이전쟁의 원인이 되었다.'
            },
        'Gemini': {
                'image' : "image/gemini.png",
                'description': '쌍둥이자리\n'
                               '\n'
                               '쌍둥이 형제인 카스토르와 폴룩스의 우애에 감동한 제우스가 이를 기리기 위해 만든 별자리이다. '
                               '카스토르와 폴룩스는 스파르타의 왕비 레다와 고니로 변신한 제우스 사이에서 태어났다. 카스토르는 말 타기에 능했고, '
                               '폴룩스는 권투와 무기 다루기에 뛰어난 재능이 있었다.'
                               '또한 폴룩스는 불사신의 몸을 가지고 있는 것으로 알려져 있다.'
                               '카스토르가 죽게 되자 폴룩스 역시 슬픔을 이기지 못하고 죽음을 선택하게 된다. 하지만 불사의 몸을 가진 폴룩스는 마음대로 죽을 수도 없는 운명이었다.'
                               '결국 폴룩스는 제우스에게 자신의 죽음을 부탁했고, '
                               '이들 형제의 우애에 감동한 제우스는 카스토르와 폴룩스를 두 개의 밝은 별로 만들어 형제의 우애를 영원히 기리도록 하였다.'
            },
        'Leo': {
                'image' : "image/leo.png",
                'description': '사자자리\n'
                               '\n'
                               '별자리 이름과 형태가 가장 적절하게 연결되는 경우로, "백수의 왕"에 걸맞게 하늘 중간에 엎드려 누운 사자의 모습을 하고 있다. '
                               '구성하는 별들도 가슴부위의 1등성 레굴루스를 비롯해 전부 1~4등성 이내의 밝은 별들로 되어 있다.\n'
                               '\n'
                               '별자리의 모델은 헤라클레스가 쓰러뜨린 네메아의 사자이고, 동서양 모두에서 황제의 별자리로 취급하고있다.'
                               ' 제우스와 알크메나 사이에서 태어난 헤르쿨레스는 제우스의 아내 헤라의 미움을 받아 12가지의 모험을 해야 했는데 '
                               '그 첫 번째가 네메아 골짜기의 사자를 죽이는 일이었다. \n'
                               '\n'
                               '유성이 변하여 된 이 사자는 지구의 사자보다 훨씬 크고, 성질도 포악하여 네메아 사람들에게 많은 고통을 주었다.'
                               '헤라클레스는 활과 창, 방망이 등을 사용하여 사자와 싸워보았지만 어떤 무기로도 결코 사자를 이길 수 없었다. '
                               '헤라클레스는 무기를 버리고 사자와 뒤엉켜 생사를 가르는 격투를 벌인 끝에 사자를 물리칠 수 있었다. '
            },
        'Orion': {
                'image' : "image/orion.png",
                'description': '오리온자리\n'
                               '\n'
                               '겨울철 별자리를 찾는데 있어 가장 기준이 되는 별자리이다. 남쪽 하늘에 밝은 별 세 개가 비스듬하게 놓여있고 '
                               '주변으로 1등성 별이 두 개나 포함되어 장구같은 모양을 이루고 있는 것이 사냥꾼 오리온자리이다. '
                               '어깨에 적색거성인 베텔게우스와 다리쪽에 리겔이 있다. 오리온대성운과 말머리성운이 오리온자리 한 가운데 아래쪽에 있다.\n'
                               '\n'
                               '그리스 신화에 오리온은 바다의 신 포세이돈의 아들로 뛰어난 사냥꾼이었다. 달과 사냥의 여신인 아르테미스는 오리온과 사랑하는 사이였으나, '
                               '아르테미스의 오빠인 아폴론은 이들의 사랑을 탐탁하지 않게 생각하였다. '
                               '오리온을 싫어하던 아폴론은 어느 날 바다 멀리서 사냥을 하고 있는 오리온을 발견하고 오리온을 과녁 삼아 동생과 내기를 청한다.'
            },
        'Scorpius': {
                'image' : "image/scorpius.png",
                'description': '전갈자리\n'
                               '\n'
                               '그리스 신화에 따르면 사냥꾼인 오리온의 자만심이 하늘을 찌를 듯 높아 "이 세상에서 자기보다 강한 자는 없다"고 거만하게 자랑하고 다녔다 한다. '
                               '이 말은 듣고 화가 난 헤라가 오리온을 죽이려고 전갈을 풀어놓았다고 한다. '
                               '그러나 전갈도 오리온 죽이지 못했고, 결국 자신의 애인인 아르테미스가 쏜 화살에 맞아 죽었다. '
                               '그러나 전갈은 오리온을 죽인 공로로 하늘의 별자리가 되었다고 한다.\n'
                               '\n'
                               '독침을 휘두르며 오리온에게 다가가는 신화 속의 전갈이 전갈자리가 되었지만, 전갈은 영원히 오리온을 죽일 수 없다. '
                               '그 이유인 즉, 밤하늘에서 전갈자리가 떠오를 때면 오리온자리가 서쪽하늘로 달아나 져버리고 전갈이 하늘을 가로질러 지하로 쫓아 내려가면 오리온은 동쪽에서 올라오기 때문이다. '
            },
        'Taurus': {
                'image' : "image/taurus.png",
                'description': '황소자리'
                               '\n'
                               '황소자리의 황소는 바람기 많은 제우스가 페니키아의 공주 유로파를 유혹하기 위해 변한 모습이다. '
                               '제우스는 바닷가에서 놀고 있는 유로파의 아름답고 우아한 모습에 반해버려 곧 사랑에 빠졌고, 유로파를 유혹하기 위해 눈부신 하얀 소로 변신하여 왕의 소떼 속으로 들어갔다.'
                               '제우스의 의도대로 유로파 공주는 많은 소들 중에서 멋진 흰 소를 발견하였고, 눈부신 소의 아름다움에 사로잡혀 흰 소 곁으로 다가갔다.'
                               '유로파가 다가가 장난치듯 황소 등에 올라타자 흰 소는 기다렸다는 듯이 바다로 뛰어들어 크레테섬까지 헤엄쳐 갔다. '
                               '크레테에 도착한 제우스는 본래의 모습을 드러내고 유로파를 설득시켜 아내로 맞이하였다.'
            },
        'Ursa Major': {
                'image' : "image/ursa_major.png",
                'description': '큰곰자리\n'
                               '\n'
                               '천구의 북극 부근에 있는 별자리이다. 곰의 모양을 한 이 별자리는 북반구 중위도 이상에서는 언제나 볼 수 있다. \n'
                               '\n'
                               '동아시아에서는 자미원의 북두, 태미원의 삼태, 주변의 작은 별자리들에 해당된다.\n'
                               '\n'
                               '큰곰자리는 부근의 작은곰자리와 함께 그리스 신화의 칼리스토의 전설과 관련되어 있다. '
                               '칼리스토는 빼어난 외모에 사냥 솜씨가 뛰어났던 아르카디아의 공주였는데 그녀의 미모에 반한 제우스는 그녀를 유혹했고, '
                               '신의 사랑을 뿌리칠 수 없었던 칼리스토는 제우스와의 사랑으로 아르카스를 낳았다. '
                               '이것을 알게 된 제우스의 아내 헤라는 칼리스토를 흰곰으로 만들었다. '
                               '엄마를 잃은 칼리스토의 아들 아르카스는 엄마의 사냥 솜씨를 이어받아 훌륭한 사냥꾼으로 자랐다\n'
                               '\n'
                               '어느날 숲 속에서 사냥 나온 아들 아르카스와 마주치게 되된 칼리스토는 너무 반가운 나머지 자신이 곰이라는 것을 잊고 아르카스을 껴안기 위해 달려들었다. '
                               '아르카스는 사나운 곰이 자신을 공격하는 것으로 생각하고 활시위를 당겼다. '
                               '이 광경을 보다 못한 제우스는 둘을 하늘에 올려 별자리로 만들었다.\n'
                               '\n'
                               '하늘로 올라간 칼리스토가 곰이 되기 전보다 더 아름답게 빛나자, 여신 헤라는 이것을 질투하였고, '
                               '대양의 신 포세이돈에게 부탁하여 이들이 물을 마시지 못하게 해달라고 부탁했다. '
                               '결국 이들 모자(母子)는 북극의 하늘만 맴돌게 되었다고 한다. '

            },
    }
    for name in filtered:
        info = constellation_info.get(name,{})
        #st.write("•", name)
        with st.expander(name):
            if info.get('image'):
                st.image(info['image'], use_container_width=True)
            st.write(info.get('description', '해당 별자리의 설명이 등록되어 있지 않습니다.'))

    st.caption(f"서버 전송할 클래스: {classes_to_send}")
else:
    st.warning("별자리가 현재 위치에서 보이지 않습니다.")

# ⑩ 이미지 업로드 및 YOLOv5 서버 호출
st.subheader("🔭 별자리 이미지 업로드 및 탐지")
uploaded = st.file_uploader("별자리 이미지 업로드", type=["jpg","png","jpeg"])
if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, caption="원본 이미지", use_container_width=True)

    # 서버 호출
    file_bytes = uploaded.getvalue()
    files = {"image": (uploaded.name, file_bytes, uploaded.type or "image/jpeg")}
    data  = [("classes", cls) for cls in classes_to_send]
    with st.spinner("탐지 중..."):
        try:
            resp = requests.post("http://127.0.0.1:5000/detect", files=files, data=data)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            st.error(f"탐지 요청 실패: {e}")
            st.stop()

    # 바운딩 박스 그리기
    draw = ImageDraw.Draw(img)
    for det in result.get("detections", []):
        x1, y1, x2, y2 = det["bbox"]
        cls_name = det["class"]
        conf     = det["confidence"]
        draw.rectangle([x1, y1, x2, y2], outline="lime", width=2)
        draw.text((x1, y1 - 10), f"{cls_name} {conf:.2f}", fill="lime")

    st.image(img, caption="탐지 결과", use_container_width=True)
