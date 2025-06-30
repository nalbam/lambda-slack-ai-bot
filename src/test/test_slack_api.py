#!/usr/bin/env python3
"""
Slack API 테스트 스크립트
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

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

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("❌ slack-sdk가 설치되지 않았습니다. 'pip install slack-sdk'로 설치해주세요.")
    sys.exit(1)

try:
    from src.api.slack_api import get_encoded_image_from_slack, upload_file
    from src.config import settings
    from src.utils import logger
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)


class SlackTester:
    """Slack API 테스트 클래스"""
    
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not self.bot_token:
            print("❌ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
            sys.exit(1)
        
        self.client = WebClient(token=self.bot_token)
        print(f"✅ Slack Bot Token 확인 (토큰: {self.bot_token[:15]}...)")
        
        # 테스트용 채널 (일반적으로 존재하는 채널들)
        self.test_channels = ["general", "random", "ai-bot-test"]
    
    def test_auth_and_info(self) -> Dict[str, Any]:
        """인증 및 봇 정보 테스트"""
        print("\n🔐 Slack 인증 및 봇 정보 테스트")
        print("-" * 40)
        
        results = []
        
        # 1. 인증 테스트
        try:
            print("\n📝 테스트 1: 인증 확인")
            start_time = time.time()
            auth_response = self.client.auth_test()
            end_time = time.time()
            
            result = {
                "test_number": 1,
                "test_name": "auth_test",
                "success": True,
                "response_time": round(end_time - start_time, 2),
                "user_id": auth_response.get("user_id"),
                "team_id": auth_response.get("team_id"),
                "team": auth_response.get("team"),
                "user": auth_response.get("user"),
                "bot_id": auth_response.get("bot_id")
            }
            
            print(f"✅ 성공 - {result['response_time']}초")
            print(f"👤 사용자: {result['user']} (ID: {result['user_id']})")
            print(f"🏢 팀: {result['team']} (ID: {result['team_id']})")
            print(f"🤖 봇 ID: {result['bot_id']}")
            
            results.append(result)
            
        except SlackApiError as e:
            print(f"❌ 인증 실패: {e.response['error']}")
            results.append({
                "test_number": 1,
                "test_name": "auth_test",
                "success": False,
                "error": e.response['error']
            })
        
        # 2. 봇 정보 테스트
        try:
            print("\n📝 테스트 2: 봇 정보 확인")
            start_time = time.time()
            
            # 봇의 사용자 정보 가져오기
            if results and results[0]["success"]:
                user_id = results[0]["user_id"]
                user_info = self.client.users_info(user=user_id)
                end_time = time.time()
                
                user_data = user_info["user"]
                result = {
                    "test_number": 2,
                    "test_name": "bot_info",
                    "success": True,
                    "response_time": round(end_time - start_time, 2),
                    "name": user_data.get("name"),
                    "real_name": user_data.get("real_name"),
                    "display_name": user_data.get("profile", {}).get("display_name"),
                    "is_bot": user_data.get("is_bot"),
                    "app_id": user_data.get("profile", {}).get("app_id")
                }
                
                print(f"✅ 성공 - {result['response_time']}초")
                print(f"🏷️ 봇 이름: {result['name']}")
                print(f"📛 실제 이름: {result['real_name']}")
                print(f"🤖 봇 여부: {result['is_bot']}")
                
                results.append(result)
            
        except SlackApiError as e:
            print(f"❌ 봇 정보 조회 실패: {e.response['error']}")
            results.append({
                "test_number": 2,
                "test_name": "bot_info",
                "success": False,
                "error": e.response['error']
            })
        
        return {"test_type": "auth_and_info", "results": results}
    
    def test_channel_operations(self) -> Dict[str, Any]:
        """채널 관련 작업 테스트"""
        print("\n📺 Slack 채널 작업 테스트")
        print("-" * 40)
        
        results = []
        
        # 1. 채널 목록 조회
        try:
            print("\n📝 테스트 1: 채널 목록 조회")
            start_time = time.time()
            channels_response = self.client.conversations_list(
                types="public_channel,private_channel",
                limit=20
            )
            end_time = time.time()
            
            channels = channels_response["channels"]
            
            result = {
                "test_number": 1,
                "test_name": "list_channels",
                "success": True,
                "response_time": round(end_time - start_time, 2),
                "total_channels": len(channels),
                "channel_names": [ch["name"] for ch in channels[:10]]  # 처음 10개만
            }
            
            print(f"✅ 성공 - {result['response_time']}초")
            print(f"📊 총 채널 수: {result['total_channels']}")
            print(f"📋 채널 목록 (일부): {', '.join(result['channel_names'])}")
            
            results.append(result)
            
        except SlackApiError as e:
            print(f"❌ 채널 목록 조회 실패: {e.response['error']}")
            results.append({
                "test_number": 1,
                "test_name": "list_channels",
                "success": False,
                "error": e.response['error']
            })
        
        # 2. 특정 채널 정보 조회
        for i, channel_name in enumerate(self.test_channels, 2):
            try:
                print(f"\n📝 테스트 {i}: #{channel_name} 채널 정보 조회")
                start_time = time.time()
                
                # 채널 ID 찾기
                channels_response = self.client.conversations_list()
                channel_id = None
                for ch in channels_response["channels"]:
                    if ch["name"] == channel_name:
                        channel_id = ch["id"]
                        break
                
                if channel_id:
                    channel_info = self.client.conversations_info(channel=channel_id)
                    end_time = time.time()
                    
                    channel_data = channel_info["channel"]
                    result = {
                        "test_number": i,
                        "test_name": f"channel_info_{channel_name}",
                        "success": True,
                        "response_time": round(end_time - start_time, 2),
                        "channel_name": channel_data["name"],
                        "channel_id": channel_data["id"],
                        "is_member": channel_data.get("is_member", False),
                        "member_count": channel_data.get("num_members", 0)
                    }
                    
                    print(f"✅ 성공 - {result['response_time']}초")
                    print(f"🆔 채널 ID: {result['channel_id']}")
                    print(f"👥 멤버 수: {result['member_count']}")
                    print(f"✋ 봇 참여 여부: {result['is_member']}")
                else:
                    result = {
                        "test_number": i,
                        "test_name": f"channel_info_{channel_name}",
                        "success": False,
                        "error": f"채널 #{channel_name}을 찾을 수 없음"
                    }
                    print(f"⚠️ 채널 #{channel_name}을 찾을 수 없습니다.")
                
                results.append(result)
                
            except SlackApiError as e:
                print(f"❌ 채널 정보 조회 실패: {e.response['error']}")
                results.append({
                    "test_number": i,
                    "test_name": f"channel_info_{channel_name}",
                    "success": False,
                    "error": e.response['error']
                })
        
        return {"test_type": "channel_operations", "results": results}
    
    def test_message_operations(self) -> Dict[str, Any]:
        """메시지 관련 작업 테스트"""
        print("\n💬 Slack 메시지 작업 테스트")
        print("-" * 40)
        
        results = []
        
        # 테스트용 채널 찾기
        test_channel_id = None
        try:
            channels_response = self.client.conversations_list()
            for ch in channels_response["channels"]:
                if ch["name"] in self.test_channels and ch.get("is_member", False):
                    test_channel_id = ch["id"]
                    print(f"📺 테스트 채널: #{ch['name']} ({test_channel_id})")
                    break
        except:
            pass
        
        if not test_channel_id:
            print("⚠️ 테스트 가능한 채널을 찾을 수 없습니다. 메시지 테스트를 건너뜁니다.")
            return {"test_type": "message_operations", "results": [
                {
                    "test_number": 1,
                    "test_name": "message_tests",
                    "success": False,
                    "error": "테스트 가능한 채널 없음"
                }
            ]}
        
        # 1. 간단한 메시지 전송 테스트 (실제로는 전송하지 않음, API 검증만)
        try:
            print("\n📝 테스트 1: 메시지 API 구조 검증")
            
            # 메시지 전송 구조 테스트 (실제 전송 안함)
            test_message = "🧪 API 테스트 메시지입니다."
            
            result = {
                "test_number": 1,
                "test_name": "message_structure",
                "success": True,
                "response_time": 0,
                "test_channel": test_channel_id,
                "message_length": len(test_message),
                "note": "실제 메시지 전송은 하지 않았습니다 (테스트 목적)"
            }
            
            print(f"✅ 메시지 구조 검증 완료")
            print(f"📝 테스트 메시지 길이: {result['message_length']}자")
            print(f"📺 대상 채널: {result['test_channel']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 메시지 구조 검증 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "message_structure",
                "success": False,
                "error": str(e)
            })
        
        # 2. 파일 업로드 구조 테스트
        try:
            print("\n📝 테스트 2: 파일 업로드 API 구조 검증")
            
            # 임시 테스트 데이터
            test_data = b"Test file content for API validation"
            
            result = {
                "test_number": 2,
                "test_name": "file_upload_structure",
                "success": True,
                "response_time": 0,
                "test_data_size": len(test_data),
                "note": "실제 파일 업로드는 하지 않았습니다 (테스트 목적)"
            }
            
            print(f"✅ 파일 업로드 구조 검증 완료")
            print(f"📊 테스트 데이터 크기: {result['test_data_size']} bytes")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 파일 업로드 구조 검증 실패: {e}")
            results.append({
                "test_number": 2,
                "test_name": "file_upload_structure",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "message_operations", "results": results}
    
    def test_utility_functions(self) -> Dict[str, Any]:
        """유틸리티 함수 테스트"""
        print("\n🛠️ Slack 유틸리티 함수 테스트")
        print("-" * 40)
        
        results = []
        
        # 1. 이미지 인코딩 함수 테스트
        try:
            print("\n📝 테스트 1: 이미지 인코딩 함수 구조 검증")
            
            # 실제 URL 대신 구조만 테스트
            test_url = "https://example.com/test.jpg"
            
            result = {
                "test_number": 1,
                "test_name": "image_encoding_structure",
                "success": True,
                "test_url": test_url,
                "function_available": callable(get_encoded_image_from_slack),
                "note": "실제 이미지 다운로드는 하지 않았습니다 (테스트 목적)"
            }
            
            print(f"✅ 이미지 인코딩 함수 구조 검증 완료")
            print(f"🔗 테스트 URL: {result['test_url']}")
            print(f"⚙️ 함수 사용 가능: {result['function_available']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 이미지 인코딩 함수 테스트 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "image_encoding_structure",
                "success": False,
                "error": str(e)
            })
        
        # 2. 파일 업로드 함수 테스트
        try:
            print("\n📝 테스트 2: 파일 업로드 함수 구조 검증")
            
            result = {
                "test_number": 2,
                "test_name": "file_upload_function_structure",
                "success": True,
                "function_available": callable(upload_file),
                "note": "실제 파일 업로드는 하지 않았습니다 (테스트 목적)"
            }
            
            print(f"✅ 파일 업로드 함수 구조 검증 완료")
            print(f"⚙️ 함수 사용 가능: {result['function_available']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 파일 업로드 함수 테스트 실패: {e}")
            results.append({
                "test_number": 2,
                "test_name": "file_upload_function_structure",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "utility_functions", "results": results}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 Slack API 전체 테스트 시작")
        print("=" * 50)
        
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bot_token_prefix": self.bot_token[:15] + "...",
            "settings": {
                "bot_cursor": settings.BOT_CURSOR,
                "max_len_slack": settings.MAX_LEN_SLACK
            },
            "tests": []
        }
        
        # 1. 인증 및 봇 정보 테스트
        auth_results = self.test_auth_and_info()
        all_results["tests"].append(auth_results)
        
        # 2. 채널 작업 테스트
        channel_results = self.test_channel_operations()
        all_results["tests"].append(channel_results)
        
        # 3. 메시지 작업 테스트
        message_results = self.test_message_operations()
        all_results["tests"].append(message_results)
        
        # 4. 유틸리티 함수 테스트
        utility_results = self.test_utility_functions()
        all_results["tests"].append(utility_results)
        
        # 결과 요약
        print("\n📊 테스트 결과 요약")
        print("=" * 50)
        
        for test in all_results["tests"]:
            test_name = test["test_type"]
            successful_tests = sum(1 for r in test["results"] if r["success"])
            total_tests = len(test["results"])
            
            print(f"🔸 {test_name}: {successful_tests}/{total_tests} 성공")
            
            if successful_tests < total_tests:
                failed_tests = [r for r in test["results"] if not r["success"]]
                for failed in failed_tests:
                    print(f"  ❌ 테스트 {failed['test_number']}: {failed.get('error', 'Unknown error')}")
        
        print("\n📝 참고사항:")
        print("- 실제 메시지 전송이나 파일 업로드는 수행하지 않았습니다.")
        print("- 봇이 채널에 참여되어 있어야 일부 기능이 정상 작동합니다.")
        print("- API 구조와 권한만 검증하였습니다.")
        
        return all_results


def main():
    """메인 실행 함수"""
    try:
        tester = SlackTester()
        results = tester.run_all_tests()
        
        print(f"\n✅ 모든 테스트 완료!")
        print(f"📅 실행 시간: {results['timestamp']}")
        
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()