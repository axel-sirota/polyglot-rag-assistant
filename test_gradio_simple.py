import gradio as gr

def greet(name):
    return f"Hello {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "__main__":
    print("Starting simple Gradio test...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
    print("Gradio launched!")