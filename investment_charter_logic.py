import json
import os

class InvestmentCharter:
    def __init__(self, username: str):
        self.username = username
        self.rules = self.load_charter()

    def load_charter(self):
        path = f"data/{self.username}_charter.json"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return [
                "충동적인 매수는 하지 않는다.",
                "손실을 두려워하지 않고 원칙대로 행동한다.",
                "정보는 검증된 출처만 참고한다."
            ]

    def add_personal_rule(self, rule_text, source="직접 추가"):
        self.rules.append(rule_text)
        self.save_charter()

    def save_charter(self):
        path = f"data/{self.username}_charter.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, ensure_ascii=False, indent=2)

def show_charter_compliance_check(username, memo):
    charter = InvestmentCharter(username)
    compliance_issues = []
    warnings = []

    for rule in charter.rules:
        if rule in memo:
            continue
        if any(keyword in memo for keyword in ["충동", "조급", "감정"]):
            compliance_issues.append(f"❌ '{rule}' 준수 여부 확인 필요")

    recommendation = "투자 전 감정 상태를 점검하고, 원칙에 기반한 판단을 하세요."

    return {
        "compliance_issues": compliance_issues,
        "warnings": warnings,
        "recommendation": recommendation
    }
