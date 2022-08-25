import './App.css';

import React, { useEffect, useRef, useState, } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Col, Container, Row } from 'react-bootstrap'

function App() {

  const [modifier, setModifier] = useState("");
  const [image, setImage] = useState("");
  const [favoriteDresses, setFavoriteDress] = useState([]);
  const [recognitionStatus, setRecognitionStatus] = useState("認識開始");
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState([]);

  const refFirstRef = useRef(true);

  // stateをセット
  const handleModifier = e => setModifier(e.target.value);
  const handleVisible = e => {
    speechText("こんなドレスはどうですか？")
    setVisible(true);
  };
  const addFavoriteDress = (newFavoriteDress) => {
    setFavoriteDress([newFavoriteDress, ...favoriteDresses])
  }

  // 読み込み時
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
      getNewImage();
    } else {
      // 更新時
      submitText();
    }
  }

  // 新しい画像を取得
  const getNewImage = async () => {
    await axios.get("http://127.0.0.1:49876/dress")
      .then((response) => {
        setImage(response.data)
        console.log(response.data)
      })
  }

  // 読み上げ
  const speechText = (text) => {
    console.log(text);
    const speech = new SpeechSynthesisUtterance();
    speech.text = text;
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
    const results = e.results[0][0].transcript;
    console.log(results);
    setModifier(results);
    console.log('stop')
    recognizer.stop();
    isListening = false;
    setRecognitionStatus("認識開始");
  }
  let isListening = false;
  const recognize = (e) => {
    if (!isListening) startRecognizer();
    console.log(isListening)
  }

  const startRecognizer = () => {
    if (isListening) return;
    console.log('start')
    recognizer.start();
    isListening = true;
    setRecognitionStatus("認識終了");
  }

  // 通信
  const API_KEY = "cd70e208-d0a2-597a-fe54-4d45b34e3556:fx"
  const API_URL = "https://api-free.deepl.com/v2/translate"
  const submitText = async () => {
    console.log(modifier)
    let content = encodeURI('auth_key=' + API_KEY + '&text=' + modifier + '&source_lang=JA&target_lang=EN');
    let url = API_URL + '?' + content;

    await axios.get(url)
      .then((responseTrans) => {
        console.log(responseTrans.data["translations"][0]["text"]);
        const modifierEng = responseTrans.data["translations"][0]["text"]
        const postData = {
          "modifier": modifierEng,
          "image_path": image
        }
        console.log(postData)
        const postUrl = "http://127.0.0.1:49876/dress"
        const result = axios.post(postUrl, postData)
          .then((responseImage) => {
            console.log(responseImage.data);
            if (responseImage.data["new_turn"]) addFavoriteDress(image);
            setImage(responseImage.data["new_image"]);
            setLoading(false);
            speechText("こちらはどうですか？")
          })
          .catch((errorImage) => {
            console.log(errorImage);
          })
      }).catch((errorTrans) => {
        console.log("Could not reach the API: ");
        console.log(errorTrans.message);
      })

    setLoading(true);
  }

  return (
    <Container>
      <Row>
        <Col md={10}>
          <div id='start' style={{ visibility: !visible ? "visible" : "hidden" }} onClick={handleVisible}>
            <button>開始</button>
          </div>
          <div className="loader" style={{ visibility: loading ? "visible" : "hidden" }}>Loading...</div>
          <div id="main" className="App" style={{ visibility: visible ? "visible" : "hidden" }}>
            <Container>
              <Row>
                <Col className='questionArea'>
                  <p>こんなドレスはどうですか？</p>
                </Col>
              </Row>
              <Row>
                <Col md={{ span: 6, offset: 2 }} className="suggestion" >
                  <img src={`${process.env.PUBLIC_URL}/images/${image}.png`} alt="suggestion" />
                </Col>
                <Col md={{ span: 2, offset: 8 }} className='modifierArea'>
                  <button onClick={recognize}>{recognitionStatus}</button>
                  <input type="text" placeholder="Enter modifier" onChange={handleModifier} />
                  <button onClick={submitText}>送信</button>
                </Col>
              </Row>
              <Row className='favoriteArea'>
                <Col md={{ span: 8, offset: 2 }}>
                  {favoriteDresses.map((favoriteDress) =>
                    <img src={`${process.env.PUBLIC_URL}/images/${favoriteDress}.png`} alt="suggestion" key={favoriteDress} className="favorite" />
                  )}
                </Col>
              </Row>
            </Container>
          </div>
        </Col>
        <Col md={2}>
        </Col>
      </Row>
    </Container>
  );
}

export default App;
