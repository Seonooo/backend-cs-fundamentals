# 백엔드 CS 기본기

Java / Spring 백엔드 개발자를 위한 CS 학습 자료입니다.
개념을 설명할 수 있고, 실무에서 만나면 알아볼 수 있는 깊이까지만 다룹니다.

**기준 환경:** Java 21 · Spring Boot 3 · MySQL 8(InnoDB). 이 조합에만 해당하는 설명은 본문에 "스프링 기본 설정에서", "InnoDB에서"처럼 조건을 붙여 표시했습니다. 버전별 세부 동작은 사용하는 JDK와 Spring Boot 버전의 공식 문서로 한 번 더 확인하세요.

**👉 사이트에서 읽기: https://seonooo.github.io/backend-cs-fundamentals/**

## 이런 분께

- CS를 교과서로 배웠지만, 톰캣·HikariCP·`@Transactional` 같은 실무 장면과 잘 연결되지 않는 신입~주니어 백엔드 개발자
- 면접에서 "왜 그런가요?"라는 꼬리 질문에 자기 말로 설명해야 하는 분

## 구성과 읽는 법

- 운영체제 → 네트워크 → 데이터베이스 → 공통 원리, **4개 영역 26편**으로 구성했습니다.
- **앞에서부터 순서대로** 읽으세요. 앞에서 배운 개념이 뒤에서 모양만 바꿔 계속 다시 나옵니다. 예를 들어 스레드 풀(07)의 패턴이 HTTP 커넥션 풀(15)과 DB 커넥션 풀(23)에서 반복됩니다.
- 각 편은 **개념 → 그림 → 실무 예시 → 설명해보기** 순서입니다. "설명해보기"는 답을 열기 전에 먼저 소리 내어 설명해 보세요.
- 마지막 26편에 전체 흐름을 모은 **연결 키워드 지도**가 있습니다.

## 목차

### 운영체제

| # | 편 | 한 줄 요약 |
|---|---|---|
| 01 | [프로세스와 스레드](https://seonooo.github.io/backend-cs-fundamentals/os/01-process-thread.html) | 스프링 서버는 프로세스 하나이고, 요청은 스레드가 처리합니다. 스레드끼리 힙을 공유한다는 점이 모든 동시성 문제의 출발점입니다. |
| 02 | [메모리 구조와 JVM 메모리](https://seonooo.github.io/backend-cs-fundamentals/os/02-memory.html) | JVM 메모리가 스택과 힙으로 어떻게 나뉘는지, GC 멈춤과 `OutOfMemoryError`가 어디서 생기는지 다룹니다. |
| 03 | [가상 메모리와 페이지 캐시](https://seonooo.github.io/backend-cs-fundamentals/os/03-virtual-memory.html) | "디스크는 엄청나게 느리고, OS는 메모리로 그 느림을 숨긴다"는 감각을 잡습니다. 인덱스와 캐시를 이해하는 바탕입니다. |
| 04 | [컨텍스트 스위칭과 CPU·I/O 바운드](https://seonooo.github.io/backend-cs-fundamentals/os/04-context-switch.html) | 코어 4개로 스레드 200개가 돌아가는 이유를 알면 "스레드를 몇 개 둘까"와 "스레드 덤프 읽기"에 답할 수 있습니다. |
| 05 | [동기화: 경쟁 조건과 락](https://seonooo.github.io/backend-cs-fundamentals/os/05-sync.html) | `count++`도 안전하지 않은 이유와 자바의 해결 도구를 봅니다. 서버가 여러 대가 되면 JVM 락이 통하지 않는 이유까지 다룹니다. |
| 06 | [데드락](https://seonooo.github.io/backend-cs-fundamentals/os/06-deadlock.html) | 락이 둘 이상이면 서로를 영원히 기다리는 상황이 생깁니다. 실무에서는 자바 코드보다 DB에서 더 자주 만납니다. |
| 07 | [스레드 풀과 비동기 처리](https://seonooo.github.io/backend-cs-fundamentals/os/07-thread-pool.html) | "만들어 두고 돌려쓴다"는 풀링 패턴을 처음 다룹니다. 풀이 작업을 받는 순서와 스프링의 `@Async`를 봅니다. |
| 08 | [가상 스레드](https://seonooo.github.io/backend-cs-fundamentals/os/08-virtual-thread.html) | Java 21 가상 스레드는 기다리는 동안 OS 스레드를 놓아 줍니다. 대신 병목이 DB 커넥션 풀 같은 다른 곳으로 옮겨갑니다. |

### 네트워크

| # | 편 | 한 줄 요약 |
|---|---|---|
| 09 | [네트워크 계층 큰 그림](https://seonooo.github.io/backend-cs-fundamentals/network/09-layers.html) | 계층 이름을 외우기보다, 에러가 났을 때 어느 계층의 문제인지 짚는 법을 다룹니다. L4와 L7 로드밸런서의 차이도 봅니다. |
| 10 | [DNS와 요청의 전체 흐름](https://seonooo.github.io/backend-cs-fundamentals/network/10-dns.html) | DNS는 여러 단계에서 캐시됩니다. 요청 하나가 응답을 받기까지 거치는 단계를 한 장으로 정리합니다. |
| 11 | [TCP·UDP와 연결 비용](https://seonooo.github.io/backend-cs-fundamentals/network/11-tcp.html) | 연결을 맺을 때 드는 왕복 시간과 끊은 뒤 남는 `TIME_WAIT`를 봅니다. keep-alive와 커넥션 풀이 존재하는 이유입니다. |
| 12 | [HTTP 기본과 멱등성](https://seonooo.github.io/backend-cs-fundamentals/network/12-http.html) | HTTP 메시지의 구조와 HTTP/1.1·2·3의 전송 방식 차이를 봅니다. 메서드와 상태 코드는 외우기보다, 재시도해도 안전한지와 누구의 잘못인지를 가리는 데 씁니다. |
| 13 | [HTTPS와 TLS](https://seonooo.github.io/backend-cs-fundamentals/network/13-https.html) | TLS가 보장하는 것과 인증서가 증명하는 것을 봅니다. 실무에서 어떤 에러로 만나는지도 다룹니다. |
| 14 | [쿠키·세션·토큰](https://seonooo.github.io/backend-cs-fundamentals/network/14-auth.html) | HTTP는 무상태라 로그인 증명을 어딘가에 보관해야 합니다. 서버가 여러 대가 되면 보관 위치의 차이가 드러납니다. |
| 15 | [HTTP 클라이언트 커넥션 풀](https://seonooo.github.io/backend-cs-fundamentals/network/15-http-pool.html) | 스레드 풀과 같은 패턴을 외부 API 연결에 적용합니다. 크기·대기·고갈이라는 같은 질문과 세 가지 타임아웃을 다룹니다. |
| 16 | [타임아웃·재시도·장애 전파](https://seonooo.github.io/backend-cs-fundamentals/network/16-timeout.html) | 외부 서비스 하나의 느림이 전체 장애로 번지는 길을 봅니다. 타임아웃·재시도·서킷 브레이커·벌크헤드로 그 길을 끊습니다. |
| 17 | [블로킹 vs 논블로킹 I/O](https://seonooo.github.io/backend-cs-fundamentals/network/17-io-model.html) | "I/O를 기다리는 스레드" 문제의 세 가지 답을 비교합니다. 스레드 풀, 가상 스레드, 이벤트 루프(WebFlux)입니다. |

### 데이터베이스

| # | 편 | 한 줄 요약 |
|---|---|---|
| 18 | [인덱스](https://seonooo.github.io/backend-cs-fundamentals/database/18-index.html) | "정렬되어 있다"는 성질 하나로 설명합니다. 어떤 쿼리가 빠르고, 어떤 쿼리가 인덱스를 못 타는지 봅니다. |
| 19 | [실행 계획 읽기](https://seonooo.github.io/backend-cs-fundamentals/database/19-explain.html) | `EXPLAIN`의 네 칸만 읽어도 대부분의 느린 쿼리 원인이 보입니다. |
| 20 | [트랜잭션과 @Transactional](https://seonooo.github.io/backend-cs-fundamentals/database/20-transaction.html) | 트랜잭션은 "전부 성공 아니면 전부 취소"입니다. 스프링 프록시 방식에서 나오는 실무 함정과 롤백 규칙을 다룹니다. |
| 21 | [격리 수준과 MVCC](https://seonooo.github.io/backend-cs-fundamentals/database/21-isolation.html) | 동시에 도는 트랜잭션끼리 서로의 변경을 언제 보는지 다룹니다. MVCC로도 못 막는 갱신 손실까지 봅니다. |
| 22 | [DB 락과 동시성 제어](https://seonooo.github.io/backend-cs-fundamentals/database/22-db-lock.html) | 재고·쿠폰·잔액을 DB 레벨에서 지키는 세 가지 방법을 비교합니다. 비관적 락, 낙관적 락, 원자적 UPDATE입니다. |
| 23 | [DB 커넥션 풀](https://seonooo.github.io/backend-cs-fundamentals/database/23-db-pool.html) | 마지막 풀입니다. 트랜잭션·락·쿼리 속도와 얽혀 있어서 서비스 전체가 멈추는 장애가 가장 자주 나는 곳입니다. |
| 24 | [JPA와 DB 기본기](https://seonooo.github.io/backend-cs-fundamentals/database/24-jpa.html) | 영속성 컨텍스트(1차 캐시)와 N+1 문제를 다룹니다. 결국 "SQL이 몇 번, 어떤 모양으로 나가는가"의 문제입니다. |
| 25 | [복제와 읽기/쓰기 분리](https://seonooo.github.io/backend-cs-fundamentals/database/25-replication.html) | 읽기를 복사본으로 나누면 부하가 줄어듭니다. 대신 방금 쓴 데이터가 안 보이는 복제 지연 문제가 따라옵니다. |

### 공통 원리

| # | 편 | 한 줄 요약 |
|---|---|---|
| 26 | [캐시](https://seonooo.github.io/backend-cs-fundamentals/common/26-cache.html) | 요청 하나가 거치는 여러 겹의 캐시를 봅니다. Cache-Aside 패턴, 로컬 캐시와 Redis의 비교, 캐시 스탬피드를 다루고 전체 연결 키워드 지도로 마무리합니다. |

## 관통하는 연결 키워드

같은 원리가 영역을 넘어 모양만 바꿔 반복됩니다. 키워드 하나를 골라 등장한 편을 순서대로 다시 읽으면 좋은 복습이 됩니다.

| 연결 키워드 | 반복되는 질문 | 등장한 편 |
|---|---|---|
| 풀링·재사용 | 비싼 자원을 몇 개 두고, 모자라면 어떻게 기다리나 | 01 → 07 → 11 → 15 → 23 |
| 공유 상태·동시성 | 여럿이 같은 값을 동시에 바꾸면? | 01 → 05 → 06 → 21 → 22 → 26(캐시 키) |
| 대기·블로킹 | 기다리는 동안 자원을 쥐고 있나? | 04 → 07 → 08 → 16 → 17 → 23 |
| 캐시·지역성 | 가까운 곳에 복사본을 두면 얼마나 빨라지나 | 03 → 10 → 18 → 24 → 26 |
| 무상태·스케일아웃 | 서버가 여러 대가 되면 "내 메모리"의 것은? | 05 → 14 → 22 → 25 → 26(로컬 캐시) |
| 장애 전파·타임아웃 | 한 곳의 느림이 어떻게 전체로 번지나 | 07 → 12 → 15 → 16 → 20 → 23 |
| 일관성 트레이드오프 | 복사본은 얼마나 늦어도 괜찮은가 | 10 → 24 → 25 → 26 |
| 프록시 함정 | 스프링이 대신 해 주는 일은 언제 적용되지 않나 | 05 → 07(@Async) → 20 → 26(@Cacheable) |

## 저장소 구조

```
docs/                              ← GitHub Pages 배포 폴더 (main 브랜치 /docs)
  index.html                       ← 목차
  os/ network/ database/ common/   ← 영역별 26편
  assets/style.css                 ← 모든 페이지 공통 스타일
```

빌드 과정이 없는 정적 HTML입니다. 저장소를 받은 뒤 `docs/index.html`을 브라우저로 열면 됩니다.
