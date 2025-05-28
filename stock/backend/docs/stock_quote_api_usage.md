# 주식 시세 REST API 사용 가이드

## 개요
이 문서는 프론트엔드에서 REST API를 사용하여 실시간 주식 시세 정보를 조회하는 방법을 설명합니다.

## API 엔드포인트

### 주식 시세 조회

```
GET /api/stocks/quote?symbol={symbol}
```

**파라미터**:
- `symbol` (필수): 조회할 주식 심볼 (예: AAPL, MSFT, GOOGL)

**응답 형식**:
```json
{
  "c": 150.75,        // 현재 가격 (Current price)
  "d": 2.25,          // 변동폭 (Change)
  "dp": 1.52,         // 변동률(%) (Percent change)
  "h": 152.3,         // 고가 (High price)
  "l": 149.1,         // 저가 (Low price)
  "o": 149.5,         // 시가 (Open price)
  "pc": 148.5,        // 전일 종가 (Previous close)
  "t": 1651234567890, // 타임스탬프 (밀리초) 
  "update_time": 1651234560 // 서버 업데이트 시간 (초)
}
```

## 사용 예시

### JavaScript Fetch API

```javascript
async function getStockQuote(symbol) {
  try {
    const response = await fetch(`http://localhost:8000/api/stocks/quote?symbol=${symbol}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('주식 시세 조회 중 오류:', error);
    return null;
  }
}

// 사용 예시
getStockQuote('AAPL')
  .then(data => {
    if (data) {
      console.log(`애플 현재가: $${data.c}`);
      console.log(`변동: ${data.d > 0 ? '+' : ''}${data.d} (${data.dp}%)`);
    }
  });
```

### React Hook 사용 예시

```jsx
import { useState, useEffect } from 'react';

function StockQuoteComponent({ symbol }) {
  const [quoteData, setQuoteData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const intervalId = setInterval(() => {
      fetch(`http://localhost:8000/api/stocks/quote?symbol=${symbol}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          if (isMounted) {
            setQuoteData(data);
            setLoading(false);
          }
        })
        .catch(err => {
          if (isMounted) {
            setError(err.message);
            setLoading(false);
          }
        });
    }, 10000); // 10초마다 업데이트

    // 컴포넌트 마운트 시 즉시 첫 번째 데이터 로드
    fetch(`http://localhost:8000/api/stocks/quote?symbol=${symbol}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (isMounted) {
          setQuoteData(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      });

    // 클린업 함수
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [symbol]);

  if (loading) {
    return <div>로딩 중...</div>;
  }

  if (error) {
    return <div>오류: {error}</div>;
  }

  if (!quoteData) {
    return <div>데이터 없음</div>;
  }

  // 가격 상승/하락에 따른 스타일 적용
  const priceChangeStyle = {
    color: quoteData.d >= 0 ? 'green' : 'red'
  };

  return (
    <div className="stock-quote">
      <h2>{symbol} 시세 정보</h2>
      <div className="price-info">
        <h3>${quoteData.c.toFixed(2)}</h3>
        <p style={priceChangeStyle}>
          {quoteData.d >= 0 ? '+' : ''}{quoteData.d.toFixed(2)} ({quoteData.dp.toFixed(2)}%)
        </p>
      </div>
      <div className="price-details">
        <div>
          <span>시가:</span>
          <span>${quoteData.o.toFixed(2)}</span>
        </div>
        <div>
          <span>고가:</span>
          <span>${quoteData.h.toFixed(2)}</span>
        </div>
        <div>
          <span>저가:</span>
          <span>${quoteData.l.toFixed(2)}</span>
        </div>
        <div>
          <span>전일 종가:</span>
          <span>${quoteData.pc.toFixed(2)}</span>
        </div>
      </div>
      <div className="update-time">
        마지막 업데이트: {new Date(quoteData.t).toLocaleTimeString()}
      </div>
    </div>
  );
}

export default StockQuoteComponent;
```

### 주식 시세 차트 예시 (Chart.js 사용)

```jsx
import { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

// Chart.js 컴포넌트 등록
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

function StockPriceChart({ symbol }) {
  const [priceHistory, setPriceHistory] = useState([]);
  const [timeLabels, setTimeLabels] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  
  // 고정된 데이터 포인트 수 관리
  const MAX_DATA_POINTS = 20;

  useEffect(() => {
    // 초기화
    setPriceHistory([]);
    setTimeLabels([]);
    
    const fetchInterval = setInterval(() => {
      fetch(`http://localhost:8000/api/stocks/quote?symbol=${symbol}`)
        .then(response => response.json())
        .then(data => {
          const price = data.c;
          const time = new Date().toLocaleTimeString();
          
          setCurrentPrice(price);
          
          // 새 데이터 추가
          setPriceHistory(prev => {
            // 최대 데이터 포인트 수 유지
            const updatedPrices = [...prev, price];
            return updatedPrices.slice(-MAX_DATA_POINTS);
          });
          
          setTimeLabels(prev => {
            const updatedLabels = [...prev, time];
            return updatedLabels.slice(-MAX_DATA_POINTS);
          });
        })
        .catch(err => console.error('주식 시세 조회 중 오류:', err));
    }, 10000); // 10초마다 업데이트
    
    // 컴포넌트 마운트 시 즉시 첫 번째 데이터 로드
    fetch(`http://localhost:8000/api/stocks/quote?symbol=${symbol}`)
      .then(response => response.json())
      .then(data => {
        const price = data.c;
        const time = new Date().toLocaleTimeString();
        
        setCurrentPrice(price);
        setPriceHistory([price]);
        setTimeLabels([time]);
      })
      .catch(err => console.error('주식 시세 조회 중 오류:', err));
      
    return () => clearInterval(fetchInterval);
  }, [symbol]);
  
  const chartData = {
    labels: timeLabels,
    datasets: [
      {
        label: `${symbol} 가격`,
        data: priceHistory,
        fill: false,
        backgroundColor: 'rgb(75, 192, 192)',
        borderColor: 'rgba(75, 192, 192, 0.8)',
        tension: 0.2
      }
    ]
  };
  
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `${symbol} 실시간 가격 차트`
      }
    },
    scales: {
      y: {
        beginAtZero: false
      }
    }
  };
  
  return (
    <div className="stock-chart">
      <h2>{symbol} 가격 차트</h2>
      {currentPrice && (
        <div className="current-price">
          현재 가격: ${currentPrice.toFixed(2)}
        </div>
      )}
      <div className="chart-container">
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  );
}

export default StockPriceChart;
```

## 실시간 업데이트에 관한 참고 사항

해당 API는 분당 최대 60회 (초당 1회) 요청을 처리할 수 있습니다. 프론트엔드에서 과도한 요청을 보내면 서버 부하가 발생할 수 있으므로 다음 지침을 따라주세요:

1. 일반적인 업데이트 간격은 10초에서 60초 사이가 적절합니다.
2. 실시간 업데이트가 필요한 경우에만 짧은 간격으로 요청하세요.
3. 사용자가 페이지나 탭을 변경했을 때는 요청을 중단하거나 간격을 늘려주세요.
4. 가상화폐와 같은 실시간성이 매우 중요한 데이터는 웹소켓(`/ws/stocks`) 연결을 사용하세요.

## 성능 최적화 방법

1. **데이터 폴링 최적화:**
   - 화면이 활성화된 경우에만 폴링
   - 여러 컴포넌트가 같은 심볼을 요청하는 경우 데이터 공유
   - `requestAnimationFrame`을 사용하여 브라우저 렌더링 주기와 일치

2. **컴포넌트 렌더링 최적화:**
   - `React.memo`나 `useMemo`, `useCallback` 활용
   - 필요한 데이터만 렌더링하는 얕은 비교 구현

3. **에러 핸들링 및 재시도 로직:**
   - 지수 백오프(exponential backoff) 알고리즘 활용
   - 네트워크 오류시 자동 재연결 구현

## 오류 처리

API 요청 시 다음과 같은 오류 상태를 처리해야 합니다:

- **404 Not Found**: 요청한 심볼이 존재하지 않는 경우
- **429 Too Many Requests**: API 요청 제한에 도달한 경우
- **500 Server Error**: 서버 내부 오류가 발생한 경우

각 오류에 대해 적절한 메시지를 사용자에게 표시하고 필요에 따라 재시도 메커니즘을 구현하세요.

## 요청 제한 및 캐싱

서버에서는 각 심볼별로 최대 분당 1회 API 요청을 수행하며 60초 동안 결과를 캐싱합니다. 클라이언트에서 자주 요청하더라도 서버는 요청 제한을 지키면서 최신 캐시 데이터를 반환합니다.

프론트엔드에서는 추가적으로 로컬 캐싱을 구현하여 네트워크 요청을 최소화할 수 있습니다.

