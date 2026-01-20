import google.generativeai as genai

class GeminiHelper:
    # 클래스 변수로 모델을 선언하여 모든 인스턴스가 공유함 (중복 연결 방지)
    _model = None 

    def __init__(self, api_key):
        """Gemini API 설정 및 초기화"""
        self.api_key = api_key
        
        # 모델이 아직 설정되지 않았을 때만 딱 한 번 실행
        if GeminiHelper._model is None and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # 가성비 좋은 2.5-flash 모델 사용
                GeminiHelper._model = genai.GenerativeModel('gemini-2.5-flash-lite')
                print("✅ Gemini 2.5 Flash-Lite 연결 성공! (최초 1회)")
            except Exception as e:
                print(f"⚠️ Gemini 설정 오류: {e}")

    def generate_comment(self, post_content, user_prompt):
        """
        블로그 본문 내용과 사용자 정의 프롬프트를 바탕으로 맞춤형 댓글 생성
        """
        # [수정 포인트] self.model이 아니라 GeminiHelper._model을 참조해야 함
        if GeminiHelper._model is None or not post_content:
            return None

        # GUI에서 설정한 프롬프트를 기본으로 사용
        base_prompt = user_prompt if user_prompt else "당신은 따뜻한 블로그 이웃입니다. 본문을 읽고 다정한 댓글을 1~2문장으로 써주세요."

        full_prompt = f"""
        {base_prompt}

        [게시글 본문]
        {post_content[:1000]}
        """

        try:
            print(f"📍 AI가 댓글 생성중입니다...")
            # [수정 포인트] GeminiHelper._model 사용
            response = GeminiHelper._model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ AI 댓글 생성 실패: {e}")
            return None