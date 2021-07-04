import construct
import uuid
import enum

MESSAGE_SIZE = 2048

class ErrorCodes(enum.IntEnum):
    OK =                        0
    UNKNOWN_ERROR =             -1
    MESSAGE_INCORRECT_SIZE =    -2
    INVALID_MESSAGE =           -3
    TIMEOUT =                   -4
    INVALID_CERTIFICATE =       -5
    UNKNOWN_CERTIFICATE =       -6
    PUBLIC_KEY_ALREADY_USED =   -7
    COMMUNICATION_ERROR =       -8

class MessageType(enum.IntEnum):
    REGISTER_CERTIFICATE = 1    # A request to register a certificate in the server (so that clients can trust it)
    VERIFY_CERTIFICATE = 2      # A request to verify a certificate
    DELETE_CERTIFICATE = 3      # A request to delete certificate
    OK = 4                      # The server reply that indicates success
    ERROR = 5                   # The server reply that indicates an error


ERROR_CODE_TO_MESSAGE = {
    ErrorCodes.OK                       : b"success",
    ErrorCodes.UNKNOWN_ERROR            : b"Unknown error",
    ErrorCodes.MESSAGE_INCORRECT_SIZE   : b"Incorrect size of message",
    ErrorCodes.INVALID_MESSAGE          : b"Invalid message",
    ErrorCodes.TIMEOUT                  : b"Request timed out",
    ErrorCodes.INVALID_CERTIFICATE      : b"Certificate is invalid",
    ErrorCodes.UNKNOWN_CERTIFICATE      : b"Certificate not found",
    ErrorCodes.PUBLIC_KEY_ALREADY_USED  : b"Public key is already used in another certificate",
    ErrorCodes.COMMUNICATION_ERROR      : b"Communication error",
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
                                        "type"              / construct.Const(MessageType.VERIFY_CERTIFICATE.value, construct.Byte),
                                        "owner_uuid"        / construct.Bytes(len(uuid.uuid4().hex)),
                                        "owner_size"        / construct.Int8ub,
                                        "owner"             / construct.Bytes(lambda ctx: ctx.owner_size),
                                        "public_key_size"   / construct.Int16ub,
                                        "public_key"        / construct.Bytes(lambda ctx: ctx.public_key_size),
                                    ))

DELETE_CERTIFICATE_MESSAGE =    construct.FixedSized(MESSAGE_SIZE,
                                    construct.Struct(
                                        "type"              / construct.Const(MessageType.DELETE_CERTIFICATE.value, construct.Byte),
                                        "owner_uuid"        / construct.Bytes(len(uuid.uuid4().hex)),
                                        "owner_size"        / construct.Int8ub,
                                        "owner"             / construct.Bytes(lambda ctx: ctx.owner_size),
                                        "private_key_size"  / construct.Int16ub,
                                        "private_key"       / construct.Bytes(lambda ctx: ctx.private_key_size),
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

