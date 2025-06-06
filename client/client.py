import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from skyfield.api import (
    load, wgs84, Star,
    load_constellation_map, load_constellation_names
)

st.set_page_config(page_title="별자리 보기", layout="centered")
st.title("🌌 현재 위치에서 보이는 별자리")

# ① 위치 받아오기
location = streamlit_geolocation()

# ② 유효성 검사
if not location or location.get("latitude") is None or location.get("longitude") is None:
    st.info("위치 정보를 아직 가져오지 못했습니다.\n브라우저에서 위치 사용을 허용해주세요.")
    st.stop()

lat = location["latitude"]
lon = location["longitude"]
st.write(f"**위도:** {lat:.6f} | **경도:** {lon:.6f}")

# ③ Skyfield 설정
ts       = load.timescale()
t        = ts.now()
eph      = load("de421.bsp")
earth    = eph["earth"]
topos    = wgs84.latlon(lat, lon)
observer = (earth + topos).at(t)

# ④ 별자리 경계 및 이름 맵
constellation_at = load_constellation_map()
names_map        = dict(load_constellation_names())

# ⑤ 지평선 위 보이는 별자리 계산
visible = set()
for ra_h in range(24):
    for dec_deg in range(-90, 91, 10):
        star = Star(ra_hours=ra_h, dec_degrees=dec_deg)
        # 관측→천구 위치(Geocentric→Barycentric→Apparent)
        astrometric = observer.observe(star).apparent()
        # 고도 계산
        alt, _, _ = astrometric.altaz()
        if alt.degrees > 0:
            # **여기를 astrometric로 바꿔야 constellation_at이 동작합니다**
            abbr = constellation_at(astrometric)
            visible.add(abbr)
# ⑦ 관심 별자리 하드코딩 필터
interest_full = ['Aquila', 'Bootes', 'Canis Major', 'Canis Minor', 'Cassiopeia', 'Cygnus', 'Gemini', 'Leo', 'Lyra', 'Orion', 'Pleiades', 'Sagittarius', 'Scorpius', 'Taurus', 'Ursa Major']  # 관심 별자리 리스트
filtered = [names_map[abbr] for abbr in visible if names_map.get(abbr) in interest_full]

# ⑧ 서버 전송용 클래스명(snake_case) 변환
classes_to_send = [name.lower().replace(' ', '_') for name in filtered]

# ⑧ 결과 출력
if filtered:
    st.subheader("현재 관측할 수 있는 별자리")
    for name in filtered:
        st.write("•", name)
    st.caption(f"서버로 전송할 클래스: {classes_to_send}")
else:
    st.warning("현재 위치에서 관측할 수 있는 별자리는 없습니다.")