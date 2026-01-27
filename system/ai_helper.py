import sys
import os

# [중요] google-genai 라이브러리 임포트
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️ [오류] 'google-genai' 라이브러리가 설치되지 않았거나 경로가 꼬였습니다.")

class GeminiHelper:
    # 클래스 변수로 클라이언트를 관리 (중복 연결 방지)
    _client = None 

    def __init__(self, api_key):
        self.api_key = api_key
        
        # 라이브러리가 없으면 초기화 중단
        if not HAS_GEMINI:
            return

        # 클라이언트가 설정되지 않았을 때만 연결
        if GeminiHelper._client is None and self.api_key:
            try:
                # [신규 방식] Client 객체 생성
                GeminiHelper._client = genai.Client(api_key=self.api_key)
                print("✅ Gemini Client 연결 성공!")
            except Exception as e:
                print(f"⚠️ Gemini 클라이언트 설정 오류: {e}")

    def generate_comment(self, post_content, user_prompt):
        """
        블로그 본문과 프롬프트를 받아 댓글 생성
        """
        # 라이브러리 없음 or 클라이언트 없음 or 본문 없음 -> 종료
        if not HAS_GEMINI or GeminiHelper._client is None or not post_content:
            return None

        # 프롬프트 설정
        base_prompt = user_prompt if user_prompt else "당신은 따뜻한 블로그 이웃입니다. 본문을 읽고 다정한 댓글을 1~2문장으로 써주세요."
        full_prompt = f"{base_prompt}\n\n[게시글 본문]\n{post_content}"

        try:
            print(full_prompt)
            print(f"📍 AI가 댓글 생성 중입니다...")
            
            # [신규 방식] 모델 호출
            response = GeminiHelper._client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=full_prompt
            )
            
            if response.text:
                return response.text.strip()
            else:
                return None
            
        except Exception as e:
            print(f"❌ AI 댓글 생성 실패: {e}")
            return None