import './App.css';

import React, { useEffect, useRef, useState, } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Col, Container, Row, Table } from 'react-bootstrap'

function App() {

  const [modifier, setModifier] = useState("");
  const [candidates, setCandidates] = useState(["B008E5Q0LG", "B00C45JBVI", "B002UNLW7K", "B00A2YDSXU", "B0035WTT2A"])
  const [image, setImage] = useState("");
  const [favoriteDresses, setFavoriteDress] = useState([]);
  const [recognitionStatus, setRecognitionStatus] = useState("認識開始");
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [voice, setVoice] = useState("");
  const [log, setLog] = useState([]);
  const [recommends, setRecommends] = useState([]);
  const [count, setCount] = useState(0);

  const refFirstRef = useRef(true);
  const recommendsRef = useRef < HTMLDivElement > (false);

  // stateをセット
  const handleVisible = () => {
    setVoice("こんなドレスはどうですか？");
    setVisible(true);
  };
  const addFavoriteDress = (newFavoriteDress) => {
    setFavoriteDress([newFavoriteDress, ...favoriteDresses])
  }
  const addLog = (record) => {
    console.log(JSON.stringify(record))
    setLog(log => {
      const newLog = [...log, JSON.stringify(record)];
      setLog(newLog);
      return newLog;
    })
  }

  useEffect(() => {
    getImage();
  }, [modifier])

  // 画像の読み込み
  const getImage = () => {
    // 一度だけ実行
    if (process.env.NODE_ENV === "development") {
      if (refFirstRef.current) {
        refFirstRef.current = false;
        return;
      }
    }

    if (modifier.length === 0) {
      // 読み込み時
      // TODO tarsが直ったらコメントアウトを消す
      //getNewImage();
    } else {
      // 更新時
      submitText();
    }
  }

  // 新しい画像を取得
  const getNewImage = async () => {
    await axios.get("http://0.0.0.0:49876/dress/start")
      .then((response) => {
        setImage(response.data)
        console.log(response.data)
        addLog(response.data);
      })
  }

  useEffect(() => {
    speechText()
  }, [voice])

  // 読み上げ
  const speechText = () => {
    console.log(voice);
    const speech = new SpeechSynthesisUtterance();
    speech.text = voice;
    speech.lang = 'ja-JP';
    window.speechSynthesis.speak(speech)
  }

  // 音声認識
  const Recognizer = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognizer = new Recognizer();
  // 言語設定
  recognizer.lang = 'ja-JP';
  // 認識
  recognizer.onresult = (e) => {
    setRecognitionStatus("読み込み中");
    const results = e.results[0][0].transcript;
    console.log(results);
    addLog(results);
    setModifier(results);
    recognizer.stop();
    isListening = false;
    if (results == modifier) submitText();
  }
  let isListening = false;
  const recognize = (e) => {
    if (!isListening) startRecognizer();
  }

  const startRecognizer = () => {
    if (isListening) return;
    recognizer.start();
    isListening = true;
    setRecognitionStatus("認識中");
  }

  // JPtext→ENtext→image
  const API_KEY = "cd70e208-d0a2-597a-fe54-4d45b34e3556:fx"
  const API_URL = "https://api-free.deepl.com/v2/translate"

  const submitText = async () => {
    console.log(modifier)
    let content = encodeURI('auth_key=' + API_KEY + '&text=' + modifier + '&source_lang=JA&target_lang=EN');
    let url = API_URL + '?' + content;

    await axios.get(url)
      .then((responseTrans) => {
        console.log(responseTrans.data["translations"][0]["text"]);
        const modifierEng = responseTrans.data["translations"][0]["text"];
        console.log(modifierEng)
        const postData = {
          "modifier": modifierEng,
          "image_path": image
        }
        switch (modifierEng) {
          case "This is good.":
          case "I like this one.":
          case "I like this dress.": {
            setCount(count + 1);
            console.log(count);
            if (count >= 2) {
              getRecommendation();
              setCount(0);
              setVoice("こちらもおすすめです");
              if (voice == "こちらもおすすめです") speechText();
              setRecognitionStatus("認識開始");
              return
            }
            console.log(postData);
            addLog(postData);
            const postUrl = "http://0.0.0.0:49876/dress/new_turn"
            const result = axios.post(postUrl, postData)
              .then((responseImage) => {
                console.log(responseImage.data);
                addLog(responseImage.data);
                if (responseImage.data["new_turn"]) {
                  addFavoriteDress(image);
                }
                setImage(responseImage.data["new_image"]);
                setLoading(false);
                setVoice("こちらはどうですか？");
                if (voice == "こちらはどうですか？") speechText();
                setRecognitionStatus("認識開始");
              })
              .catch((errorImage) => {
                console.log(errorImage);
                addLog(errorImage)
              })
            break
          }

          default:
            console.log(postData);
            addLog(postData);
            const postUrl = "http://0.0.0.0:49876/dress"
            const result = axios.post(postUrl, postData)
              .then((responseImage) => {
                console.log(responseImage.data);
                addLog(responseImage.data);
                if (responseImage.data["new_turn"]) {
                  addFavoriteDress(image);
                }
                setImage(responseImage.data["new_image"]);
                setLoading(false);
                setVoice("こちらはどうですか？");
                if (voice == "こちらはどうですか？") speechText();
                setRecognitionStatus("認識開始");
              })
              .catch((errorImage) => {
                console.log(errorImage);
                addLog(errorImage)
              })
        }
      }).catch((errorTrans) => {
        console.log("Could not reach the API: ");
        console.log(errorTrans.message);
        addLog(errorTrans.message)
      })

    setLoading(true);
  }

  const screenHeight = window.innerHeight;

  // 好み推定
  const getRecommendation = async () => {
    console.log(recommends)
    const url = 'http://0.0.0.0:49876/favorite';
    await axios.get(url)
      .then((responseRecommend) => {
        setLoading(false);
        console.log(responseRecommend.data['estimation']);
        setRecommends(responseRecommend.data['estimation']);
      })
  }

  useEffect(() => {
    const handleClickToCloseRecommends = (event) => {
      const element = recommendsRef.current;
      if (element?.contains(event.target)) return;
      setRecommends([]);
    };

    window.addEventListener("click", handleClickToCloseRecommends);
    return () => {
      window.removeEventListener("click", handleClickToCloseRecommends);
    };
  }, [recommendsRef]);

  return (
    <Container>
      <Row>
        <Col md={8}>
          <div id='start' style={{ display: !visible ? "block" : "none" }} onClick={handleVisible}>
            <button>開始</button>
          </div>
          <div className="loader" style={{ visibility: loading ? "visible" : "hidden" }}>Loading...</div>
          <div id="main" className="App" style={{ visibility: visible ? "visible" : "hidden" }}>
            <Row>
              <Col className='questionArea'>
                <p>{voice}</p>
              </Col>
            </Row>
            <Row>
              <Col md={{ span: 3 }}></Col>
              <Col className="suggestion" >
                {candidates.map((candidate) =>
                  <img src={`${process.env.PUBLIC_URL}/images/${candidate}.png`} alt="suggestion" />
                )}
              </Col>
            </Row>
            <Row>
            </Row>
            <Row>
              <Col md={{ span: 4 }}>
                <button onClick={getRecommendation}>おすすめを見る</button>
              </Col>
              <Col></Col>
              <Col md={{ span: 4 }}>
                <button onClick={recognize} className="recognize">{recognitionStatus}</button>
              </Col>
              <Recommend recommends={recommends} />
            </Row>
            <Row className='favoriteArea'>
              <Col md={{ span: 8, offset: 2 }}>
                {favoriteDresses.map((favoriteDress) =>
                  <img src={`${process.env.PUBLIC_URL}/images/${favoriteDress}.png`} alt="suggestion" key={favoriteDress} className="favorite" />
                )}
              </Col>
            </Row>
          </div>
        </Col>
        <Col md={4} style={{ height: screenHeight }} className='logArea'>
          <Log log={log} visible={visible} />
        </Col>
      </Row>
    </Container>
  );
}

const Log = (props) => {
  return (
    <Table style={{ visibility: props.visible ? "visible" : "hidden" }}>
      <tbody>
        {props.log.map(record =>
          <tr>
            <td>
              {record}
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  )
}

const Recommend = (props) => {
  return (
    <div id='recommendation'>
      {
        props.recommends.map(recommend =>
          <img src={`${process.env.PUBLIC_URL}/images/${recommend}.png`} alt="recommendation" />
        )
      }
    </div>
  )
}

export default App;
