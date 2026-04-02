import subprocess
import sys
import os
from glob import glob

# ────────────────────────────────────────────────────────────────────────────────
# 설정값
# ────────────────────────────────────────────────────────────────────────────────
PYTHON_VERSION = '3.14' 
APP_FILE       = 'DDAS.py'
REQUIREMENTS   = [
    'streamlit', 'pandas', 'geopandas', 'folium', 
    'streamlit-folium', 'scikit-learn', 'shapely', 
    'sqlalchemy', 'pymysql', 'numpy', 'plotly'
]

def run_cmd(command, capture=False):
    """
    셸 명령어를 실행한다. 상황에 따라 결과를 반환하거나 실시간으로 출력한다.

    Parameters
    ----------------------
    command : str
        실행할 셸 명령어.
    capture : bool, optional
        True이면 결과를 변수에 담아 반환(화면 출력X), 
        False이면 터미널에 실시간으로 로그를 출력(화면 출력O).

    Returns
    ----------------------
    subprocess.CompletedProcess
        실행 결과 객체. capture=True일 때 stdout에 텍스트가 담긴다.
    """
    current_encoding = None if os.name == 'nt' else 'utf-8'
    
    return subprocess.run(
        command,
        shell=True,
        capture_output=capture,
        text=True,
        encoding=current_encoding
    )

def get_env_list():
    """
    현재 Conda 가상환경 목록을 가져온다.
    """
    # 목록을 읽어와야 하므로 capture=True 사용
    result = run_cmd('conda env list', capture=True)
    if result.stdout:
        return [
            line.split()[0] for line in result.stdout.split('\n')
            if line.strip() and not line.startswith('#')
        ]
    return []

def step_create_env(env_name, python_version):
    """
    가상환경을 생성한다.
    """
    print(f"\n[ 1단계 ] 가상환경 확인 중: {env_name}")
    if env_name in get_env_list():
        print(f"  '{env_name}' 환경 이미 존재 → 스킵")
        return

    print(f"  '{env_name}' 환경 생성 중 (Python {python_version})...")
    # 생성 과정을 눈으로 봐야 하므로 capture=False (기본값)
    result = run_cmd(f'conda create -n {env_name} python={python_version} -y')

    if result.returncode == 0:
        print(f"  '{env_name}' 환경 생성 완료")
    else:
        print(f"  환경 생성 실패 → 종료")
        sys.exit(1)

def step_install_packages(env_name, requirements):
    """
    패키지를 설치한다.
    """
    print(f"\n[ 2단계 ] 패키지 설치 확인 및 진행...")
    # 설치 과정을 눈으로 봐야 하므로 capture=False (기본값)
    for pkg in requirements:
        print(f"  '{pkg}' 설치 중...")
        run_cmd(f'conda run -n {env_name} pip install {pkg} -q')
    print("  모든 패키지 설치 완료")

def step_run_app(env_name, app_file):
    """
    Streamlit 앱을 실행한다.
    """
    print(f"\n[ 3단계 ] '{app_file}' 실행 시도 중...")
    abs_path = os.path.abspath(app_file)
    if not os.path.exists(abs_path):
        print(f"  오류: '{app_file}' 파일이 없다.")
        return

    # 로그 캡처 방지 및 브라우저 강제 오픈
    cmd = f'conda run --no-capture-output -n {env_name} streamlit run "{abs_path}" --server.headless=false'
    
    try:
        subprocess.Popen(cmd, shell=True, stdout=None, stderr=None)
        print(f"  서버가 시작되었다. 터미널 로그를 확인해라.")
    except Exception as e:
        print(f"  실행 중 오류: {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 메인 실행부
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("   프로젝트 환경 설정 및 앱 실행")
    print("=" * 50)

    ENV_NAME = input("▶ 가상환경 이름을 입력해라: ").strip()
    if not ENV_NAME:
        print("이름을 입력하지 않아 종료한다.")
        sys.exit(1)

    step_create_env(ENV_NAME, PYTHON_VERSION)
    step_install_packages(ENV_NAME, REQUIREMENTS)
    step_run_app(ENV_NAME, APP_FILE)

    print("\n" + "=" * 50)
    print("   모든 프로세스 완료")
    print("=" * 50)