#!/usr/bin/env python3
"""
텔레그램 바카라 게임 봇 실행 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n봇이 종료되었습니다.")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        sys.exit(1)

