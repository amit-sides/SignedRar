import os
import json
import zipfile
import threading
import time

import PySimpleGUI as sg

from common import messages
from ZipSigner import certificate
from ZipSigner import communication
from ZipSigner import signed_zip

CERTIFICATES_LIST = os.path.join("ZipSigner", "certificates.json")
GENERATED_CERTIFICATE = None
CERTIFICATES = []
LOADING_THREAD_RUNNING = False

def get_generate_keys_tab():
    certificate_details = sg.Column(element_justification="left", size=(300, 100), layout=[
                                [sg.Text("Owner: "), sg.Text(key="-CERTIFICATE_OWNER-", size=(250, None))],
                                [sg.Text("UUID: "), sg.Text(key="-CERTIFICATE_UUID-", size=(250, None))],
                                [sg.Text("Public Key: "), sg.Text(key="-CERTIFICATE_PUBLIC_KEY-", size=(250, None))]
                            ])

    generate_keys_layout = [
        [sg.Text("Owner: "), sg.Input(size=(40, None), key="-GENERATE_OWNER-", enable_events=True)],
        [sg.Button("Generate Keys", key="-GENERATE-", disabled=True)],
        [sg.Button("Register Certificate", key="-REGISTER-", disabled=True)],
        [sg.Column(element_justification="left", layout=[[certificate_details]], size=(300, 100))]
    ]

    return sg.Tab("Generate RSA keys", generate_keys_layout, element_justification="center")

def get_sign_zip_tab():
    certificate_details = sg.Column(element_justification="left", size=(355, 120), layout=[
        [sg.Text("Certificate: "), sg.Combo([], size=(35, None), key="-SIGN_CERTIFICATE-", enable_events=True)],
        [sg.Text("Owner: "), sg.Text(key="-SIGN_CERTIFICATE_OWNER-", size=(250, None))],
        [sg.Text("UUID: "), sg.Text(key="-SIGN_CERTIFICATE_UUID-", size=(250, None))],
        [sg.Text("Public Key: "), sg.Text(key="-SIGN_CERTIFICATE_PUBLIC_KEY-", size=(250, None))]
    ])

    sign_zip_layout = [
        [sg.Text("ZIP file: "), sg.Input(key="-SIGN_ZIP-", size=(30, None), enable_events=True),
                              sg.FileBrowse(key="-SIGN_BROWSE-", file_types=(("Zip Files", "*.zip"),))],
        [certificate_details],
        [sg.Button("Sign ZIP", key="-SIGN-", disabled=True)],
    ]

    return sg.Tab("Sign ZIP", sign_zip_layout, element_justification="center")

def get_verify_zip_tab():
    certificate_details = sg.Column(element_justification="left", size=(355, 80), layout=[
        [sg.Text("Owner: "), sg.Text(key="-VERIFY_CERTIFICATE_OWNER-", size=(250, None))],
        [sg.Text("UUID: "), sg.Text(key="-VERIFY_CERTIFICATE_UUID-", size=(250, None))],
    ])

    sign_zip_layout = [
        [sg.Text("ZIP file: "), sg.Input(key="-VERIFY_ZIP-", size=(30, None), enable_events=True),
                                sg.FileBrowse(key="-VERIFY_BROWSE-", file_types=(("Zip Files", "*.zip"),))],
        [sg.Button("Verify ZIP", key="-VERIFY-", disabled=True)],
        [certificate_details],
    ]

    return sg.Tab("Verify ZIP", sign_zip_layout, element_justification="center")

def get_layout():
    generate_keys_tab = get_generate_keys_tab()
    sign_zip_tab = get_sign_zip_tab()
    verify_zip_tab = get_verify_zip_tab()
    tab_group = sg.TabGroup([[generate_keys_tab, sign_zip_tab, verify_zip_tab]])
    layout = [[
                    sg.Column(element_justification="center", layout=[
                                [sg.T("Registered Certificates:")],
                                [sg.Listbox([], size=(None, 10), key="-CERTIFICATES-", enable_events=True)],
                                [sg.Button("Delete Certificate", key="-DELETE-", disabled=True)]
                              ]),
                    tab_group
             ]]
    return layout

def add_certificate(window, certificate):
    global CERTIFICATES
    CERTIFICATES.append(certificate)
    window["-CERTIFICATE_OWNER-"].update(value=certificate.owner)
    window["-CERTIFICATE_UUID-"].update(value=certificate.uuid)
    window["-CERTIFICATE_PUBLIC_KEY-"].update(value=certificate.export_public()[-33:] + " ...")
    update_certificates(window)

def remove_certificate(window, certificate):
    global CERTIFICATES
    CERTIFICATES.remove(certificate)
    update_certificates(window)

def update_certificates(window):
    save_certificates()

    window["-SIGN_CERTIFICATE-"].update(values=CERTIFICATES)
    window["-CERTIFICATES-"].update(values=CERTIFICATES)

def validate_buttons(window, values):
    sign_zip_invalid = not os.path.isfile(values["-SIGN_ZIP-"]) or not values["-SIGN_ZIP-"].lower().endswith(".zip")
    window["-SIGN-"].update(disabled=sign_zip_invalid or values["-SIGN_CERTIFICATE-"] is None or values["-SIGN_CERTIFICATE-"] == "")

    verify_zip_invalid = not os.path.isfile(values["-VERIFY_ZIP-"]) or not values["-VERIFY_ZIP-"].lower().endswith(".zip")
    window["-VERIFY-"].update(disabled=verify_zip_invalid)

def generate_thread(owner):
    global GENERATED_CERTIFICATE, LOADING_THREAD_RUNNING

    GENERATED_CERTIFICATE = certificate.Certificate.generate(owner)
    LOADING_THREAD_RUNNING = False


def display_gui():
    global GENERATED_CERTIFICATE, CERTIFICATES, LOADING_THREAD_RUNNING

    sg.theme('TealMono')
    layout = get_layout()

    window = sg.Window("ZIP Signer", layout, icon="ZipSigner.ico", finalize=True)
    update_certificates(window)

    while True:  # Event Loop
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            break
        if event == "-GENERATE_OWNER-":
            window["-GENERATE-"].update(disabled=len(values["-GENERATE_OWNER-"]) <= 0)
        if event == "-GENERATE-":
            owner = values["-GENERATE_OWNER-"]
            if len(owner) > 32:
                sg.popup_error(f"Owner too long! current length: {len(owner)}, needs to be less than 32.", title="Owner too long!")
            else:
                window["-GENERATE-"].update(disabled=True)
                LOADING_THREAD_RUNNING = True
                t = threading.Thread(target=generate_thread, args=(owner,))
                t.start()
                current_value = "Generating..."
                while LOADING_THREAD_RUNNING:
                    window["-GENERATE-"].update(text=current_value)
                    window.refresh()
                    time.sleep(0.3)
                    current_value += "."
                window["-REGISTER-"].update(disabled=False)
                window["-GENERATE-"].update(text="Generate Keys")
                sg.popup_ok(f"RSA keys have been generated successfully for '{owner}' !\nYou can now register your certificate with the server.", title="Generated :)")
        elif event == "-REGISTER-":
            if GENERATED_CERTIFICATE:
                result, error = GENERATED_CERTIFICATE.register()
                if result:
                    add_certificate(window, GENERATED_CERTIFICATE)
                    window["-REGISTER-"].update(disabled=True)
                    sg.popup_ok(f"Certificate has been registered successfully for '{GENERATED_CERTIFICATE.owner}' !", title="Registered :)")
                    GENERATED_CERTIFICATE = None
                else:
                    sg.popup_error(error[1].decode("utf-8") + f"\nerror code: {error[0]}")
        elif event == "-CERTIFICATES-":
            window["-DELETE-"].update(disabled=len(values["-CERTIFICATES-"]) <= 0)
        elif event == "-DELETE-":
            for c in values["-CERTIFICATES-"]:
                return_code, response, error_message = communication.delete_certificate(c)
                if return_code == messages.ErrorCodes.OK:
                    if values["-SIGN_CERTIFICATE-"] == c:
                        values["-SIGN_CERTIFICATE-"] = ""
                        window["-SIGN_CERTIFICATE-"].update(value="")
                        validate_buttons(window, values)
                    remove_certificate(window, c)
                else:
                    sg.popup_error(error_message.decode("utf-8") + f"\nerror code: {return_code}")
            window["-DELETE-"].update(disabled=True)
        elif event == "-SIGN_CERTIFICATE-" or event == "-SIGN_ZIP-" or event == "-VERIFY_ZIP-":
            validate_buttons(window, values)
            if values["-SIGN_CERTIFICATE-"]:
                window["-SIGN_CERTIFICATE_OWNER-"].update(value=values["-SIGN_CERTIFICATE-"].owner)
                window["-SIGN_CERTIFICATE_UUID-"].update(value=values["-SIGN_CERTIFICATE-"].uuid)
                window["-SIGN_CERTIFICATE_PUBLIC_KEY-"].update(value=values["-SIGN_CERTIFICATE-"].export_public()[-33:] + " ...")
        elif event == "-SIGN-":
            try:
                with signed_zip.SignedZip(values["-SIGN_ZIP-"], "a") as zip:
                    zip.sign(values["-SIGN_CERTIFICATE-"])
                sg.popup_ok(f"The file {values['-SIGN_ZIP-']} has been signed successfully!", title="Signed :)")
            except (zipfile.BadZipfile, zipfile.LargeZipFile) as e:
                sg.popup_error(f"The file {values['-SIGN_ZIP-']} is either not a ZIP or too large.", title="Error")
        elif event == "-VERIFY-":
            try:
                with signed_zip.SignedZip(values["-VERIFY_ZIP-"], "r") as zip:
                    signature_valid = zip.verify()
                if signature_valid:
                    return_code, response, error_message = communication.verify_certificate(zip.certificate)
                    if return_code == messages.ErrorCodes.OK:
                        window["-VERIFY_CERTIFICATE_OWNER-"].update(value=zip.certificate.owner)
                        window["-VERIFY_CERTIFICATE_UUID-"].update(value=zip.certificate.uuid)
                        sg.popup_ok(f"The file {values['-VERIFY_ZIP-']} has been verified successfully!", title="Verified :)")
                    else:
                        sg.popup_error(error_message.decode("utf-8") + f"\nerror code: {return_code}")
                else:
                    sg.popup_error(f"The file {values['-VERIFY_ZIP-']} doesn't have a valid signature.", title="Not Verified!")

            except (zipfile.BadZipfile, zipfile.LargeZipFile) as e:
                sg.popup_error(f"The file {values['-VERIFY_ZIP-']} is either not a ZIP or too large.", title="Error")

    window.close()

def load_certificates():
    global CERTIFICATES

    if os.path.exists(CERTIFICATES_LIST) and os.path.isfile(CERTIFICATES_LIST):
        with open(CERTIFICATES_LIST, "rb") as db:
            certificates = json.loads(db.read())
            CERTIFICATES = [certificate.Certificate.from_dict(d) for d in certificates]

def save_certificates():
    with open(CERTIFICATES_LIST, "wb") as db:
        certificates = [c.to_dict() for c in CERTIFICATES]
        db.write(json.dumps(certificates).encode("utf-8"))

def main():
    load_certificates()
    communication.init()
    display_gui()


if __name__ == "__main__":
    main()
