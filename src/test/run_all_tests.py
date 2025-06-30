#!/usr/bin/env python3
"""
모든 AI API 테스트를 실행하는 통합 스크립트
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv가 설치되지 않았습니다. 'pip install python-dotenv'로 설치해주세요.")
    sys.exit(1)

# 환경 변수 로드
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    print("⚠️ .env.local 파일이 없습니다. 환경 변수가 시스템에서 로드됩니다.")

# 테스트 모듈들 import
try:
    from test_openai_api import OpenAITester
    from test_gemini_api import GeminiTester
    from test_slack_api import SlackTester
    from test_workflow import WorkflowTester
except ImportError as e:
    print(f"❌ 테스트 모듈 import 실패: {e}")
    print("💡 src/test 디렉토리에서 스크립트를 실행해주세요.")
    sys.exit(1)


class IntegratedTester:
    """통합 AI API 테스터"""
    
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": self._check_environment(),
            "tests": []
        }
        
        print("🚀 AI API 통합 테스트 시작")
        print("=" * 60)
        print(f"📅 시작 시간: {self.results['timestamp']}")
        print(f"🌐 환경 상태: {self.results['environment']}")
    
    def _check_environment(self) -> Dict[str, Any]:
        """환경 설정 확인"""
        env_status = {
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "gemini_api_key": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            "slack_bot_token": bool(os.getenv("SLACK_BOT_TOKEN")),
            "slack_signing_secret": bool(os.getenv("SLACK_SIGNING_SECRET")),
            "env_file_exists": env_file.exists()
        }
        
        return env_status
    
    def run_openai_tests(self) -> Dict[str, Any]:
        """OpenAI API 테스트 실행"""
        print("\n🤖 OpenAI API 테스트 실행")
        print("-" * 40)
        
        if not self.results["environment"]["openai_api_key"]:
            print("⚠️ OpenAI API 키가 설정되지 않았습니다. 테스트를 건너뜁니다.")
            return {
                "test_suite": "openai",
                "skipped": True,
                "reason": "API key not configured"
            }
        
        try:
            tester = OpenAITester()
            results = tester.run_all_tests()
            results["test_suite"] = "openai"
            results["skipped"] = False
            return results
        except Exception as e:
            print(f"❌ OpenAI 테스트 실행 실패: {e}")
            return {
                "test_suite": "openai",
                "skipped": False,
                "error": str(e),
                "success": False
            }
    
    def run_gemini_tests(self) -> Dict[str, Any]:
        """Gemini API 테스트 실행"""
        print("\n🧠 Gemini API 테스트 실행")
        print("-" * 40)
        
        if not self.results["environment"]["gemini_api_key"]:
            print("⚠️ Gemini API 키가 설정되지 않았습니다. 테스트를 건너뜁니다.")
            return {
                "test_suite": "gemini",
                "skipped": True,
                "reason": "API key not configured"
            }
        
        try:
            tester = GeminiTester()
            results = tester.run_all_tests()
            results["test_suite"] = "gemini"
            results["skipped"] = False
            return results
        except Exception as e:
            print(f"❌ Gemini 테스트 실행 실패: {e}")
            return {
                "test_suite": "gemini",
                "skipped": False,
                "error": str(e),
                "success": False
            }
    
    def run_slack_tests(self) -> Dict[str, Any]:
        """Slack API 테스트 실행"""
        print("\n💬 Slack API 테스트 실행")
        print("-" * 40)
        
        if not self.results["environment"]["slack_bot_token"]:
            print("⚠️ Slack Bot Token이 설정되지 않았습니다. 테스트를 건너뜁니다.")
            return {
                "test_suite": "slack",
                "skipped": True,
                "reason": "Bot token not configured"
            }
        
        try:
            tester = SlackTester()
            results = tester.run_all_tests()
            results["test_suite"] = "slack"
            results["skipped"] = False
            return results
        except Exception as e:
            print(f"❌ Slack 테스트 실행 실패: {e}")
            return {
                "test_suite": "slack",
                "skipped": False,
                "error": str(e),
                "success": False
            }
    
    def run_workflow_tests(self) -> Dict[str, Any]:
        """워크플로우 테스트 실행"""
        print("\n⚙️ 워크플로우 엔진 테스트 실행")
        print("-" * 40)
        
        try:
            tester = WorkflowTester()
            results = tester.run_all_tests()
            results["test_suite"] = "workflow"
            results["skipped"] = False
            return results
        except Exception as e:
            print(f"❌ 워크플로우 테스트 실행 실패: {e}")
            return {
                "test_suite": "workflow",
                "skipped": False,
                "error": str(e),
                "success": False
            }
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """전체 테스트 결과 요약 리포트 생성"""
        summary = {
            "total_test_suites": len(self.results["tests"]),
            "successful_suites": 0,
            "skipped_suites": 0,
            "failed_suites": 0,
            "suite_details": [],
            "environment_issues": [],
            "recommendations": []
        }
        
        # 각 테스트 스위트 분석
        for test_result in self.results["tests"]:
            suite_name = test_result.get("test_suite", "unknown")
            
            if test_result.get("skipped", False):
                summary["skipped_suites"] += 1
                summary["suite_details"].append({
                    "suite": suite_name,
                    "status": "skipped",
                    "reason": test_result.get("reason", "Unknown")
                })
            elif test_result.get("error"):
                summary["failed_suites"] += 1
                summary["suite_details"].append({
                    "suite": suite_name,
                    "status": "failed",
                    "error": test_result.get("error", "Unknown error")
                })
            else:
                # 성공한 테스트 스위트 - 세부 결과 분석
                suite_tests = test_result.get("tests", [])
                total_tests = 0
                successful_tests = 0
                
                for test_group in suite_tests:
                    test_results = test_group.get("results", [])
                    total_tests += len(test_results)
                    successful_tests += sum(1 for r in test_results if r.get("success", False))
                
                summary["successful_suites"] += 1
                summary["suite_details"].append({
                    "suite": suite_name,
                    "status": "completed",
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": round(successful_tests / total_tests * 100, 1) if total_tests > 0 else 0
                })
        
        # 환경 문제 식별
        env = self.results["environment"]
        if not env["env_file_exists"]:
            summary["environment_issues"].append("💡 .env.local 파일이 없습니다.")
        if not env["openai_api_key"]:
            summary["environment_issues"].append("🔑 OpenAI API 키가 설정되지 않았습니다.")
        if not env["gemini_api_key"]:
            summary["environment_issues"].append("🔑 Gemini API 키가 설정되지 않았습니다.")
        if not env["slack_bot_token"]:
            summary["environment_issues"].append("🔑 Slack Bot Token이 설정되지 않았습니다.")
        
        # 추천사항 생성
        if summary["skipped_suites"] > 0:
            summary["recommendations"].append("⚡ 건너뛴 테스트가 있습니다. 환경 설정을 확인해주세요.")
        if summary["failed_suites"] > 0:
            summary["recommendations"].append("🔧 실패한 테스트가 있습니다. 에러 메시지를 확인하고 문제를 해결해주세요.")
        if summary["successful_suites"] == summary["total_test_suites"]:
            summary["recommendations"].append("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        
        return summary
    
    def save_results_to_file(self, filename: str = None) -> str:
        """테스트 결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        results_file = project_root / "src" / "test" / filename
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            return str(results_file)
        except Exception as e:
            print(f"❌ 결과 파일 저장 실패: {e}")
            return ""
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        start_time = time.time()
        
        # 1. OpenAI 테스트
        openai_results = self.run_openai_tests()
        self.results["tests"].append(openai_results)
        
        # 2. Gemini 테스트  
        gemini_results = self.run_gemini_tests()
        self.results["tests"].append(gemini_results)
        
        # 3. Slack 테스트
        slack_results = self.run_slack_tests()
        self.results["tests"].append(slack_results)
        
        # 4. 워크플로우 테스트
        workflow_results = self.run_workflow_tests()
        self.results["tests"].append(workflow_results)
        
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        
        # 요약 리포트 생성
        summary = self.generate_summary_report()
        self.results["summary"] = summary
        self.results["total_execution_time"] = total_time
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 전체 테스트 결과 요약")
        print("=" * 60)
        
        print(f"⏱️ 총 실행 시간: {total_time}초")
        print(f"📦 테스트 스위트: {summary['total_test_suites']}개")
        print(f"✅ 성공: {summary['successful_suites']}개")
        print(f"⏭️ 건너뜀: {summary['skipped_suites']}개")
        print(f"❌ 실패: {summary['failed_suites']}개")
        
        print("\n📋 스위트별 상세 결과:")
        for detail in summary["suite_details"]:
            suite = detail["suite"].upper()
            status = detail["status"]
            
            if status == "completed":
                success_rate = detail["success_rate"]
                print(f"  🔸 {suite}: {detail['successful_tests']}/{detail['total_tests']} 성공 ({success_rate}%)")
            elif status == "skipped":
                print(f"  ⏭️ {suite}: 건너뜀 - {detail['reason']}")
            elif status == "failed":
                print(f"  ❌ {suite}: 실패 - {detail['error'][:50]}...")
        
        if summary["environment_issues"]:
            print("\n⚠️ 환경 설정 문제:")
            for issue in summary["environment_issues"]:
                print(f"  {issue}")
        
        if summary["recommendations"]:
            print("\n💡 추천사항:")
            for rec in summary["recommendations"]:
                print(f"  {rec}")
        
        # 결과 파일 저장
        results_file = self.save_results_to_file()
        if results_file:
            print(f"\n💾 상세 결과가 저장되었습니다: {results_file}")
        
        return self.results


def main():
    """메인 실행 함수"""
    try:
        tester = IntegratedTester()
        results = tester.run_all_tests()
        
        print(f"\n🎯 통합 테스트 완료!")
        print(f"📅 완료 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 전체 성공 여부 판단
        summary = results["summary"]
        if summary["failed_suites"] == 0 and summary["successful_suites"] > 0:
            print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
            return 0
        else:
            print("⚠️ 일부 테스트에서 문제가 발생했습니다. 상세 결과를 확인해주세요.")
            return 1
        
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 통합 테스트 실행 중 오류 발생: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)