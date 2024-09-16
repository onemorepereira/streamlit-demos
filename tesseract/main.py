from PIL import Image
import boto3
import io
import json
import logging
import os
import pytesseract
import streamlit as st


logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s', level=logging.INFO)

AWS_ACCESS_KEY_ID     = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN     = os.getenv('AWS_SESSION_TOKEN')
AWS_DEFAULT_REGION    = os.getenv('AWS_DEFAULT_REGION')

def extract_text_from_image(image_bytes):
    image_stream = io.BytesIO(image_bytes)
    image        = Image.open(image_stream)
    text         = pytesseract.image_to_string(image, lang='eng', config='--oem 1')
    
    return text

def summarize_content(session, input: str, classification: str):
    bedrock  = session.client('bedrock-runtime')
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'  # Replace with the correct model ID for Claude Sonnet
    
    payload =  {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5000,
                "temperature": 0.5,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": input},
                            {"type": "text", "text": "The above text was captured via OCR from an original document."},
                            {"type": "text", "text": "The content has been classified --> {}".format(classification)},
                            {"type": "text", "text": "Rewrite the content in such a way that its easy to understand by a person. Use markdown for readability."},
                            ]
                        }
                    ]
                }

    response = bedrock.invoke_model(
        modelId=model_id,
        contentType='application/json',
        body=json.dumps(payload)
    )

    response_body = response['body']
    response_data = json.loads(response_body.read().decode('utf-8'))

    logging.info(response_data['content'][0]['text'])
    output_text = response_data['content'][0]['text']
    return output_text

def document_classifier(session, input: str):
    bedrock  = session.client('bedrock-runtime')
    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'  # Replace with the correct model ID for Claude Sonnet
    
    payload =  {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": input},
                            {"type": "text", "text": "Determine what category the content falls under."},
                            {"type": "text", "text": "Just return the classification of the document. Nothing more."},
                            ]
                        }
                    ]
                }

    response = bedrock.invoke_model(
        modelId=model_id,
        contentType='application/json',
        body=json.dumps(payload)
    )

    response_body = response['body']
    response_data = json.loads(response_body.read().decode('utf-8'))

    logging.info(response_data['content'][0]['text'])
    output_text = response_data['content'][0]['text']
    return output_text

def legibility_gate(session, input: str):
    bedrock  = session.client('bedrock-runtime')
    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'  # Replace with the correct model ID for Claude Sonnet
    
    payload =  {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": input},
                            {"type": "text", "text": "Does the above content make sense? Respond with a single word: \"YES\" or \"NO\""},
                            ]
                        }
                    ]
                }
    response = bedrock.invoke_model(
        modelId=model_id,
        contentType='application/json',
        body=json.dumps(payload)
    )

    response_body = response['body']
    response_data = json.loads(response_body.read().decode('utf-8'))

    logging.info(response_data['content'][0]['text'])
    output_text = response_data['content'][0]['text']
    return output_text

def prompt(session, input: str, prompt: str):
    bedrock  = session.client('bedrock-runtime')
    model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'  # Replace with the correct model ID for Claude Sonnet
    
    payload =  {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": input},
                            {"type": "text", "text": prompt},
                            ]
                        }
                    ]
                }

    response = bedrock.invoke_model(
        modelId=model_id,
        contentType='application/json',
        body=json.dumps(payload)
    )

    response_body = response['body']
    response_data = json.loads(response_body.read().decode('utf-8'))

    logging.info(response_data['content'][0]['text'])
    output_text = response_data['content'][0]['text']
    return output_text
    
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_SESSION_TOKEN and AWS_DEFAULT_REGION:
    pass
    
else:
    AWS_ACCESS_KEY_ID       = st.text_input('AWS_ACCESS_KEY_ID', type='password')
    AWS_SECRET_ACCESS_KEY   = st.text_input('AWS_SECRET_ACCESS_KEY', type='password')
    AWS_SESSION_TOKEN       = st.text_input('AWS_SESSION_TOKEN', type='password')
    AWS_DEFAULT_REGION      = st.selectbox("REGION", options=["us-east-1", "us-west-2"], index=0)
    
    session = boto3.Session(
        aws_access_key_id     = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
        aws_session_token     = AWS_SESSION_TOKEN,
        region_name           = AWS_DEFAULT_REGION
        )


file = st.file_uploader("Choose an image to upload", accept_multiple_files=False, type=['png', 'gif', 'jpg', 'tiff', 'jpeg'])
if file:
    logging.info(file)
    try:
        bytes_data = file.getvalue()
        with st.spinner("Applying OCR to the document"):
            text = extract_text_from_image(bytes_data)
        
        st.image(bytes_data)
        st.write("Content Extracted")
        st.info(text)
        
        st.write("OCR Quality Gate")
        with st.spinner("Determining document legibility"):
            legibility = legibility_gate(session=session, input=text)
        st.success(legibility)

        st.write("Document Classification")
        if legibility == 'YES':
            with st.spinner("Classifying the document"):
                classification = document_classifier(session=session, input=text)
            st.success(classification)
            with st.spinner("Summarizing content"):
                summarization  = summarize_content(session=session, input=text, classification=classification)
            st.success(summarization)
            question = st.text_input("Ask a question about the document")
            if question:
                response = prompt(session=session, input=summarization, prompt=question)
                st.info(response)
            
        else:
            st.warning("Poor document OCR")
        
    except Exception as e:
        logging.error(e)
        st.error(e)
