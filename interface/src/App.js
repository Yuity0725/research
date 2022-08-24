import './App.css';

import React, { useEffect, useState, } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Col, Container, Row } from 'react-bootstrap'

function App() {

  const [modifier, setModifier] = useState("a");
  const [image, setImage] = useState("");
  const [favoriteDresses, setFavoriteDress] = useState([]);

  // stateをセット
  const handleModifier = e => setModifier(e.target.value);
  const addFavoriteDress = (newFavoriteDress) => {
    setFavoriteDress([newFavoriteDress, ...favoriteDresses])
  }

  // 読み込み時
  useEffect(() => {
    getNewImage()
  }, [])

  // 新しい画像を取得
  const getNewImage = async () => {
    await axios.get("http://127.0.0.1:49876/dress")
      .then((response) => {
        setImage(response.data)
        console.log(response.data)
      })
  }

  // 通信
  const API_KEY = "cd70e208-d0a2-597a-fe54-4d45b34e3556:fx"
  const API_URL = "https://api-free.deepl.com/v2/translate"
  const submitText = async () => {
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
          })
          .catch((errorImage) => {
            console.log(errorImage);
          })
      }).catch((errorTrans) => {
        console.log("Could not reach the API: ");
        console.log(errorTrans.message);
      })
  }

  return (
    <div className="App">
      <Container>
        <Row>
          <Col className='questionArea'>
            <p>こんなドレスはどうですか？</p>
          </Col>
        </Row>
        <Row>
          <Col md={{ span: 6, offset: 2 }}>
            <img src={`${process.env.PUBLIC_URL}/images/${image}.png`} alt="suggestion" className="suggestion" />
          </Col>
          <Col md={{ span: 2, offset: 8 }} className='modifierArea'>
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
  );
}

export default App;
