import construct
import uuid
import enum

MESSAGE_SIZE = 256

class ErrorCodes(enum.IntEnum):
    OK =                        0
    UNKNOWN_ERROR =             -1
    MESSAGE_INCORRECT_SIZE =    -2
    INVALID_MESSAGE =           -3
    TIMEOUT =                   -4
    INVALID_CERTIFICATE =       -5
    UNKNOWN_CERTIFICATE =       -6
    PUBLIC_KEY_ALREADY_USED =   -7

class MessageType(enum.IntEnum):
    REGISTER_CERTIFICATE = 1    # A request to register a certificate in the server (so that clients can trust it)
    VERIFY_CERTIFICATE = 2      # A request to verify a certificate
    OK = 3                      # The server reply that indicates success
    ERROR = 4                   # The server reply that indicates an error


ERROR_CODE_TO_MESSAGE = {
    ErrorCodes.OK                       : "success",
    ErrorCodes.UNKNOWN_ERROR            : "Unknown error",
    ErrorCodes.MESSAGE_INCORRECT_SIZE   : "Incorrect size of message",
    ErrorCodes.INVALID_MESSAGE          : "Invalid message",
    ErrorCodes.TIMEOUT                  : "Request timed out",
    ErrorCodes.INVALID_CERTIFICATE      : "Certificate is invalid",
    ErrorCodes.UNKNOWN_CERTIFICATE      : "Certificate not found",
    ErrorCodes.PUBLIC_KEY_ALREADY_USED  : "Public key is already used in another certificate"
}


GENERIC_MESSAGE =               construct.FixedSized(MESSAGE_SIZE,
                                    construct.Struct(
                                        "type"  / construct.Enum(construct.Byte, MessageType),
                                        "data"  / construct.Bytes(MESSAGE_SIZE - construct.Byte.sizeof())
                                    ))

REGISTER_CERTIFICATE_MESSAGE =  construct.FixedSized(MESSAGE_SIZE,
                                    construct.Struct(
                                        "type"              / construct.Const(MessageType.REGISTER_CERTIFICATE.value, construct.Byte),
                                        "owner_size"        / construct.Int8ub,
                                        "owner"             / construct.Bytes(lambda ctx: ctx.owner_size),
                                        "public_key_size"   / construct.Int16ub,
                                        "public_key"        / construct.Bytes(lambda ctx: ctx.public_key_size),
                                    ))

VERIFY_CERTIFICATE_MESSAGE =    construct.FixedSized(MESSAGE_SIZE,
                                    construct.Struct(
                                        "type"              / construct.Const(MessageType.REGISTER_CERTIFICATE.value, construct.Byte),
                                        "owner_uuid"        / construct.Bytes(len(uuid.uuid4().hex)),
                                        "owner_size"        / construct.Int8ub,
                                        "owner"             / construct.Bytes(lambda ctx: ctx.owner_size),
                                        "public_key_size"   / construct.Int16ub,
                                        "public_key"        / construct.Bytes(lambda ctx: ctx.public_key_size),
                                    ))

OK_MESSAGE =                    construct.FixedSized(MESSAGE_SIZE,
                                    construct.Struct(
                                        "type"          / construct.Const(MessageType.OK.value, construct.Byte),
                                        "owner_uuid"    / construct.Bytes(len(uuid.uuid4().hex)),
                                    ))

ERROR_MESSAGE =                 construct.FixedSized(MESSAGE_SIZE,
                                    construct.Struct(
                                        "type"                  / construct.Const(MessageType.ERROR.value, construct.Byte),
                                        "error_code"            / construct.Int32sb,
                                        "error_message_size"    / construct.Int32ub,
                                        "error_message"         / construct.Bytes(lambda ctx: ctx.error_message_size),
                                    ))

