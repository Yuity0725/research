import React, { useEffect, useState } from 'react';
import Form from 'react-bootstrap/Form';
import axios from 'axios';

const Main = (props) => {
    const [modifier, setModifier] = useState("a");
    const [image, setImage] = useState("B00A0I8AGS");

    const handleModifier = e => setModifier(e.target.value);

    // 読み込み時
    useEffect(() => {
        getNewImage()
    }, [])

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
                    })
                    .catch((errorImage) => {
                        console.log(errorImage);
                    })
            }).catch((errorTrans) => {
                console.log("Could not reach the API: ");
                console.log(errorTrans.message);
            })
    }

    const getNewImage = async () => {
        await axios.get("http://127.0.0.1:49876/dress")
            .then((response) => {
                setImage(response.data)
            })
    }

    return (
        <div className='border'>
            <p>こんなドレスはどうですか？</p>
            <img src={`${process.env.PUBLIC_URL}/images/${image}.png`} alt="suggestion" />
            <Form.Control type="text" placeholder="Enter modifier" onChange={handleModifier} />
            <button onClick={submitText}>送信</button>
        </div>
    )
}

export default Main