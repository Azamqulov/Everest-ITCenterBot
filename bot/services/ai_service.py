import os
import re
import logging
from typing import List, Dict, Any, Optional
from bot.config import settings
from bot.services.db import db

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.prompt_version = "v1"
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "v1_channel_post.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return "Mavzu: {topic}\nIltimos, 3 ta variant tayyorlang."

    async def generate_channel_posts(
        self,
        topic: str,
        target: str = "Umumiy ta'lim va qiziqtirish",
        tone: str = "Do'stona va motivatsion",
        language: str = "uz"
    ) -> List[str]:
        """
        Generate 3-4 variants for channel post with Claude -> Gemini fallback.
        """
        prompt = (
            self.prompt_template
            .replace("{topic}", topic)
            .replace("{target}", target)
            .replace("{tone}", tone)
            .replace("{language}", language)
        )

        variants = []
        # 1. Try Claude API
        if settings.ANTHROPIC_API_KEY:
            try:
                logger.info("Calling Claude API for channel post generation...")
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
                variants = self._parse_variants(text)

                await self._log_ai_call(
                    provider="claude",
                    model="claude-3-5-sonnet",
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens,
                    status="success"
                )
                if variants:
                    return variants
            except Exception as e:
                logger.warning(f"Claude API failed: {e}. Attempting Gemini fallback...")
                await self._log_ai_call(provider="claude", model="claude-3-5-sonnet", status="failed", error=str(e))

        # 2. Try Gemini API fallback
        if settings.GEMINI_API_KEY:
            try:
                logger.info("Calling Gemini API fallback...")
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = await model.generate_content_async(prompt)
                text = response.text
                variants = self._parse_variants(text)

                await self._log_ai_call(
                    provider="gemini",
                    model="gemini-1.5-flash",
                    status="fallback_success"
                )
                if variants:
                    return variants
            except Exception as e:
                logger.warning(f"Gemini API failed: {e}")
                await self._log_ai_call(provider="gemini", model="gemini-1.5-flash", status="failed", error=str(e))

        # 3. High quality structured local template fallback if no external API key is active
        return self._generate_fallback_variants(topic)

    def _parse_variants(self, text: str) -> List[str]:
        parts = re.split(r"===\s*VARIANT\s*\d+\s*===", text, flags=re.IGNORECASE)
        variants = [p.strip() for p in parts if p.strip()]
        return variants if variants else [text.strip()]

    def _generate_fallback_variants(self, topic: str) -> List[str]:
        """Provides instant high-quality templates if external APIs are not yet configured."""
        v1 = (
            f"🚀 <b>Zamonaviy IT dunyosiga ilk qadam: {topic}!</b>\n\n"
            f"Bugungi kunda har bir muvaffaqiyatli mutaxassis texnologiyalar tilini bilishi shart. "
            f"<b>Everest IT Center</b> jamoasi bilan birgalikda orzuingizdagi IT kasbini egallang!\n\n"
            f"💡 <i>Nega aynan biz?</i>\n"
            f"• Tajribali mentorlar va real amaliy loyihalar\n"
            f"• Zamonaviy o'quv dasturlari va qulay muhit\n"
            f"• Karyera markazi va ishga joylashishda ko'mak\n\n"
            f"📍 Toshkent sh., Everest IT Center\n"
            f"📞 Aloqa: +998 71 200 00 00\n"
            f"👉 Kurslarga yozilish: @{settings.BOT_USERNAME}"
        )

        v2 = (
            f"🔥 <b>{topic} bo'yicha kuchli mutaxassis bo'lishni xohlaysizmi?</b>\n\n"
            f"Ko'pchilik dasturlashni boshlash qiyin deb o'ylaydi, ammo to'g'ri tizim va professional ustoz bilan hammasi oson! "
            f"Everest IT Center'da darslar interaktiv tarzda o'tiladi.\n\n"
            f"✅ Bepul sinov darsiga yoziling va o'z imkoniyatlaringizni sinab ko'ring!\n\n"
            f"📞 Bog'lanish: +998 71 200 00 00\n"
            f"🤖 Botimiz orqali test topshiring va ball yig'ing: @{settings.BOT_USERNAME}"
        )

        v3 = (
            f"📌 <b>IT sohasida natijaga erishish siri — amaliyotda!</b>\n\n"
            f"Bugungi kunda <b>{topic}</b> yo'nalishidagi mutaxassislarga talab kundan-kunga ortib bormoqda. "
            f"O'z kelajagingizga investitsiya qiling va yangi pog'onaga ko'tariling!\n\n"
            f"🎓 Everest IT Center — cho'qqilarni zabt etuvchilar makoni!\n\n"
            f"Batafsil ma'lumot va arizalar uchun:\n"
            f"👉 @{settings.BOT_USERNAME}\n"
            f"📞 +998 71 200 00 00"
        )
        return [v1, v2, v3]

    async def _log_ai_call(
        self,
        provider: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        status: str = "success",
        error: Optional[str] = None
    ):
        try:
            await db.execute("""
                INSERT INTO ai_logs (provider, model, prompt_version, tokens_in, tokens_out, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (provider, model, self.prompt_version, tokens_in, tokens_out, status, error))
        except Exception as e:
            logger.error(f"Failed to log AI call: {e}")

ai_service = AIService()
