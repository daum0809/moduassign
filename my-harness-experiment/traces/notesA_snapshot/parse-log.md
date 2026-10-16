1) 접근법: test_parse.py를 먼저 읽고 정규식 `^시간 ERROR [모듈] 메시지$`로 줄 시작을 매칭해 ERROR 레벨만 추출, CLI는 `|`를 `\|`로 이스케이프한 마크다운 표로 출력(sample.log의 소문자 error·CRITICAL·메시지 속 "ERROR"·트레이스백 줄은 자동 제외).
2) 오류: 테스트 실패는 없었음(python test_parse.py 2건 모두 OK). 유일한 오류는 bash heredoc에 f-string의 `{r['time']}`가 들어가자 도구가 "Contains brace with quote character"로 명령을 거부한 것(테스트 결과가 아니라 도구 응답으로 확인).
3) 해결: 파일은 heredoc 대신 Write 도구로 만들고, f-string 대신 `"| " + " | ".join(...) + " |"` 형태를 사용한 뒤 Bash로 테스트만 실행.
