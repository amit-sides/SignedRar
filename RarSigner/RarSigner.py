
import PySimpleGUI as sg

def get_generate_keys_tab():
    certificate_details = sg.Column(element_justification="left", size=(200, 100), layout=[
                                [sg.Text("Owner: "), sg.Text(key="-CERTIFICATE_OWNER-")],
                                [sg.Text("UUID: "), sg.Text(key="-CERTIFICATE_UUID-")],
                                [sg.Text("Public Key: "), sg.Text(key="-CERTIFICATE_PUBLIC_KEY-")]
                            ])

    generate_keys_layout = [
        [sg.Text("Owner: "), sg.Input(size=(40, None), key="-GENERATE_OWNER-")],
        [sg.Button("Generate Keys", key="-GENERATE-")],
        [sg.Button("Register Certificate", key="-REGISTER-")],
        [sg.Column(element_justification="left", layout=[[certificate_details]], size=(300, 100))]
    ]

    return sg.Tab("Generate RSA keys", generate_keys_layout, element_justification="center")

def get_sign_winrar_tab():
    certificate_details = sg.Column(element_justification="left", size=(355, 80), layout=[
        [sg.Text("Certificate: "), sg.Combo(["Cert1", "Cert2", "Cert3"], size=(35, None), key="-SIGN_CERTIFICATE-")],
        [sg.Text("Owner: "), sg.Text(key="-SIGN_CERTIFICATE_OWNER-")],
        [sg.Text("UUID: "), sg.Text(key="-SIGN_CERTIFICATE_UUID-")],
        [sg.Text("Public Key: "), sg.Text(key="-SIGN_CERTIFICATE_PUBLIC_KEY-")]
    ])

    sign_winrar_layout = [
        [sg.Text("WinRar: "), sg.Input(key="-SIGN_WINRAR-", size=(30, None)), sg.FileBrowse(key="-SIGN_BROWSE-")],
        [certificate_details],
        [sg.Button("Sign WinRar", key="-SIGN-")],
    ]

    return sg.Tab("Sign WinRar", sign_winrar_layout, element_justification="center")

def get_verify_winrar_tab():
    certificate_details = sg.Column(element_justification="left", size=(355, 80), layout=[
        [sg.Text("Owner: "), sg.Text(key="-VERIFY_CERTIFICATE_OWNER-")],
        [sg.Text("UUID: "), sg.Text(key="-VERIFY_CERTIFICATE_UUID-")],
    ])

    sign_winrar_layout = [
        [sg.Text("WinRar: "), sg.Input(key="-VERIFY_WINRAR-", size=(30, None)), sg.FileBrowse(key="-VERIFY_BROWSE-")],
        [sg.Button("Verify WinRar", key="-VERIFY-")],
        [certificate_details],
    ]

    return sg.Tab("Verify WinRar", sign_winrar_layout, element_justification="center")

def get_layout():
    generate_keys_tab = get_generate_keys_tab()
    sign_winrar_tab = get_sign_winrar_tab()
    verify_winrar_tab = get_verify_winrar_tab()
    tab_group = sg.TabGroup([[generate_keys_tab, sign_winrar_tab, verify_winrar_tab]])
    layout = [[
                    sg.Column(element_justification="center", layout=[
                                [sg.T("Registered Certificates:")],
                                [sg.Listbox([str(i) for i in range(3)], size=(None, 10), key="-CERTIFICATES-")],
                                [sg.Button("Delete Certificate", key="-DELETE-")]
                              ]),
                    tab_group
             ]]
    return layout

def display_gui():
    layout = get_layout()

    window = sg.Window("WinRar Signer", layout, finalize=True)

    while True:  # Event Loop
        event, values = window.read(timeout=1000)
        if event == sg.WIN_CLOSED or event == "Exit":
            break
        if event == "-UPDATE-":
            pass
        elif event == "-LAUNCH-":
            break
        elif event == "-AUTO-":
            pass
        elif event == "-QUERY_SERVER-":
            pass
        elif event == "__TIMEOUT__":
            # Timeout has passed
            pass

    window.close()

def main():
    display_gui()

if __name__ == "__main__":
    main()