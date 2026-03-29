import streamlit as st
import numpy as np
import pandas as pd
import folium
from sklearn.neighbors import BallTree
import os

st.set_page_config(layout="wide")

BASE     = os.path.join(os.path.dirname(__file__), '..')
map_path = os.path.join(BASE, 'map.html')

# ── 카테고리 → 데이터 파일 매핑 ──────────────────────────────────────
CATEGORY_FILES = {
    '전력시설':           ['data/electricity/df_substation.csv'],
    '정보통신시설':        ['data/telecommunication/df_core_통신망.csv'],
    '국가 공공기관 시설':  ['data/public/df_core_중앙행정기관.csv'],
    '교통 항공 항만 시설': ['data/transportation/df_core_공항.csv',
                            'data/transportation/df_core_지하철.csv',
                            'data/transportation/df_core_철도.csv'],
    '수원 시설':           ['data/water/df_water.csv'],
    '지하공동구':          ['data/infra/df_infra.csv'],
    '산업 시설':           ['data/factory/df_factory.csv'],
    '기지국':              ['data/frequency/df_frequency.csv'],
    '병원':                ['data/hospital/df_hospital.csv'],
    '과학연구':            ['data/science/df_과학연구시설.csv'],
    '교정 시설':           ['data/prison/df_교정시설.csv'],
    '방송시설':            ['data/broadcast/df_방송.csv'],
}


def building_cover(coords_grid, coords_building, RANGE_KM): # 제거 예정
    grid_rad     = np.deg2rad(coords_grid)
    building_rad = np.deg2rad(coords_building)
    tree         = BallTree(building_rad, metric='haversine')
    indices      = tree.query_radius(grid_rad, r=RANGE_KM / 6371)
    return pd.DataFrame({
        'grid_id':          range(len(coords_grid)),
        'building_count':   [len(idx) for idx in indices],
        'building_indices': indices,
    })


def grid_cover_single(center_coord, all_coords, RANGE_KM): #제거 예정
    all_rad    = np.deg2rad(all_coords)
    center_rad = np.deg2rad(np.array(center_coord)).reshape(1, -1)
    tree       = BallTree(all_rad, metric='haversine')
    indices    = tree.query_radius(center_rad, r=RANGE_KM / 6371)[0]
    return indices[~np.all(all_coords[indices] == np.array(center_coord), axis=1)]


def calc_score(dfs, df_grid, RANGE_KM):
    lat_min = df_grid['sw_lat'].min()
    lat_max = df_grid['ne_lat'].max()
    lon_min = df_grid['sw_lng'].min()
    lon_max = df_grid['ne_lng'].max()

    df_building = pd.concat([
        df[(df['latitude'].between(lat_min, lat_max)) &
           (df['longitude'].between(lon_min, lon_max))]
        for df in dfs.values()
    ], ignore_index=True)

    if df_building.empty:
        return pd.DataFrame({
            'grid_id':          range(len(df_grid)),
            'score':            0.0,
            'building_count':   0,
            'building_indices': [np.array([], dtype=int)] * len(df_grid),
        })

    df_result        = building_cover(
        df_grid[['center_lat', 'center_lng']].values,
        df_building[['latitude', 'longitude']].values,
        RANGE_KM,
    )
    scores_arr       = df_building['score'].values
    df_result['score'] = [scores_arr[cover].sum() for cover in df_result['building_indices']]
    return df_result


def calc_rank(dfs, df_grid, RANGE_KM, radar_num): # 기존 함수 모듈 구성 시 제거 예정

    rank_dic = {}
    dfs_temp = {key: df.copy() for key, df in dfs.items()}

    for _ in range(radar_num):
        df_result   = calc_score(dfs_temp, df_grid, RANGE_KM)
        max_score   = df_result['score'].max()
        best_points = list(df_result[df_result['score'] == max_score].index)

        if len(best_points) != 1:
            cover_list = []
            for point in best_points:
                center_coord = df_grid.loc[point, ['center_lat', 'center_lng']].values
                all_coords   = df_grid[['center_lat', 'center_lng']].values
                pos_indices  = grid_cover_single(center_coord, all_coords, RANGE_KM)
                cover_list.append(df_grid.index[pos_indices])

            best_idx      = max(range(len(cover_list)), key=lambda x: len(cover_list[x]))
            position_grid = best_points[best_idx]
            rank_dic[position_grid] = cover_list[best_idx]
            pos = df_grid.loc[position_grid, ['center_lat', 'center_lng']].values
        else:
            pos           = df_grid.loc[best_points[0], ['center_lat', 'center_lng']].values
            all_coords    = df_grid[['center_lat', 'center_lng']].values
            pos_indices   = grid_cover_single(pos, all_coords, RANGE_KM)
            rank_dic[best_points[0]] = df_grid.index[pos_indices]

        all_building_coords  = pd.concat(dfs_temp.values())[['latitude', 'longitude']].values
        building_pos_indices = grid_cover_single(pos, all_building_coords, RANGE_KM)
        covered_set          = set(map(tuple, all_building_coords[building_pos_indices]))

        for key in dfs_temp:
            dfs_temp[key] = dfs_temp[key][~dfs_temp[key].apply(
                lambda r: (r['latitude'], r['longitude']) in covered_set, axis=1
            )]

    return rank_dic


def calc_rank_for_viz(dfs, df_grid, RANGE_KM, radar_num): # 함수에서 점수 반환시 제거 예정

    rank_dic  = calc_rank(dfs, df_grid, RANGE_KM, radar_num)
    df_scores = calc_score(dfs, df_grid, RANGE_KM)   

    rows = []
    for rank, grid_id in enumerate(rank_dic.keys(), start=1):
        rows.append({
            'rank':    rank,
            'grid_id': grid_id,
            'score':   round(float(df_scores.at[grid_id, 'score']), 5),
            'lat':     df_grid.loc[grid_id, 'center_lat'],
            'lng':     df_grid.loc[grid_id, 'center_lng'],
        })

    return pd.DataFrame(rows)



@st.cache_data
def load_data(weight_items: tuple) -> dict:
    dfs = {}
    for cat, weight in weight_items:
        if weight <= 0 or cat not in CATEGORY_FILES:
            continue
        frames = []
        for rel_path in CATEGORY_FILES[cat]:
            full_path = os.path.join(BASE, rel_path)
            if not os.path.exists(full_path):
                continue
            try:
                df = pd.read_csv(full_path)
                if 'latitude' not in df.columns or 'longitude' not in df.columns:
                    continue
                df = df[['latitude', 'longitude']].dropna().copy()
                df['score'] = float(weight)
                frames.append(df)
            except Exception:
                continue
        if frames:
            dfs[cat] = pd.concat(frames, ignore_index=True)
    return dfs


@st.cache_data
def load_grid() -> pd.DataFrame:
    path = os.path.join(BASE, 'data/grid/grid_50m_18417cells.csv')
    return pd.read_csv(path)


# ── UI 렌더링 함수 ────────────────────────────────────────────────────

def render_map(col):
    with col:
        if os.path.exists(map_path):
            with open(map_path, 'r', encoding='utf-8') as f:
                html = f.read()
            st.components.v1.html(html, height=700)
        else:
            st.info("지도가 표시됩니다.")


def render_input_summary(col):
    with col:
        data = st.session_state.get('user_input')

        if data is None:
            st.info('사용자 입력 페이지에서 값을 입력하고 Select를 눌러주세요.')
            return

        with st.container(border=True):
            st.markdown('#### 입력 요약')
            c1, c2 = st.columns(2)
            c1.metric('사정 거리', f"{data['range_km']} km")
            c2.metric('후보지 수', f"{data['radar_num']} 개")

        active = {cat: w for cat, w in data['selected_weights'].items() if w > 0}

        with st.container(border=True):
            st.markdown(f'#### 선택 카테고리  `{len(active)}개`')
            if active:
                for cat, w in sorted(active.items(), key=lambda x: x[1], reverse=True):
                    bar_pct = int(w * 100 / max(active.values()) * 100) / 100
                    st.markdown(
                        f"""
                        <div style="margin-bottom:6px">
                            <div style="display:flex; justify-content:space-between; font-size:13px">
                                <span>{cat}</span>
                                <span style="color:#888">{w:.5f}</span>
                            </div>
                            <div style="background:#e0e0e0; border-radius:4px; height:8px">
                                <div style="width:{bar_pct}%; background:#4c8bf5;
                                            border-radius:4px; height:8px"></div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption('선택된 카테고리가 없습니다.')

        st.write('')
        if st.button("계산 실행", type="primary", use_container_width=True):
            range_km  = float(data['range_km'])
            radar_num = int(data['radar_num'])
            weights   = {k: v for k, v in data['selected_weights'].items() if v > 0}

            with st.spinner("후보지 계산 중"):
                dfs     = load_data(tuple(sorted(weights.items())))
                df_grid = load_grid()
                df_rank = calc_rank_for_viz(dfs, df_grid, range_km, radar_num)

                st.session_state['calc_results'] = {
                    'df_rank':   df_rank,
                    'dfs':       dfs,
                    'range_km':  range_km,
                    'radar_num': radar_num,
                    'weights':   weights,
                }
            st.success("계산 완료!")

        # 계산 결과가 있을 때만 시나리오 저장 UI 표시
        if st.session_state.get('calc_results'):
            st.divider()
            st.markdown("#### 시나리오 저장")
            name = st.text_input("시나리오 이름", placeholder="예) 방송 중심, 사정거리 1.5km")
            if st.button("저장", use_container_width=True):
                if not name.strip():
                    st.warning("시나리오 이름을 입력하세요.")
                else:
                    scenario = {'name': name.strip(), **st.session_state['calc_results']}
                    scenarios = st.session_state.get('scenarios', [])
                    # 같은 이름이면 덮어쓰기
                    scenarios = [s for s in scenarios if s['name'] != name.strip()]
                    scenarios.append(scenario)
                    st.session_state['scenarios'] = scenarios
                    st.success(f"'{name.strip()}' 저장 완료! (총 {len(scenarios)}개)")


def main():
    with st.container():
        col1, col2 = st.columns([6, 3])
        render_map(col1)
        render_input_summary(col2)


main()
