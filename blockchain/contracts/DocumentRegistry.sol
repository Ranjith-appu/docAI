// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title DocumentRegistry
 * @dev Cryptographic registry for identity and travel document screening records.
 *      STRICT ZERO-PII RULE: No personal identifiable information (name, date of birth,
 *      biometrics, document images, or document numbers) is ever stored on-chain.
 *      Only cryptographic SHA-256 / Keccak-256 hashes, timestamps, and advisory risk codes are recorded.
 */
contract DocumentRegistry {
    address public owner;

    struct DocumentRecord {
        bytes32 caseHash;          // Keccak256 hash of the unique Case ID
        bytes32 documentHash;      // SHA-256 hash of the primary uploaded document file
        bytes32 verificationHash;  // Hash of the full screening verification payload
        uint8 riskScore;           // Normalized risk score (0 - 100)
        uint256 timestamp;         // Block timestamp of registration
        address registeredBy;      // Wallet address of the submitting officer/system
        bool exists;               // Existence flag
    }

    // Mapping: caseHash => DocumentRecord
    mapping(bytes32 => DocumentRecord) private records;

    // Mapping: documentHash => caseHash (to check if a document has been screened before)
    mapping(bytes32 => bytes32) private documentToCase;

    // Events
    event DocumentRegistered(
        bytes32 indexed caseHash,
        bytes32 indexed documentHash,
        bytes32 verificationHash,
        uint8 riskScore,
        uint256 timestamp,
        address indexed registeredBy
    );

    event DocumentVerified(
        bytes32 indexed caseHash,
        bytes32 indexed documentHash,
        bool matched,
        uint256 timestamp,
        address indexed verifiedBy
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only registry owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Register a document screening record
     * @param _caseHash Hash of the case ID
     * @param _documentHash SHA-256 hash of the document binary
     * @param _verificationHash Hash of the screening verification result
     * @param _riskScore Advisory risk score (0-100)
     */
    function registerDocument(
        bytes32 _caseHash,
        bytes32 _documentHash,
        bytes32 _verificationHash,
        uint8 _riskScore
    ) external returns (bool) {
        require(_caseHash != bytes32(0), "Invalid case hash");
        require(_documentHash != bytes32(0), "Invalid document hash");
        require(!records[_caseHash].exists, "Case record already registered");

        records[_caseHash] = DocumentRecord({
            caseHash: _caseHash,
            documentHash: _documentHash,
            verificationHash: _verificationHash,
            riskScore: _riskScore,
            timestamp: block.timestamp,
            registeredBy: msg.sender,
            exists: true
        });

        documentToCase[_documentHash] = _caseHash;

        emit DocumentRegistered(
            _caseHash,
            _documentHash,
            _verificationHash,
            _riskScore,
            block.timestamp,
            msg.sender
        );

        return true;
    }

    /**
     * @notice Verify document integrity by checking if documentHash matches registered record for caseHash
     * @param _caseHash Hash of the case ID
     * @param _documentHash SHA-256 hash of the document currently presented
     */
    function verifyDocument(
        bytes32 _caseHash,
        bytes32 _documentHash
    ) external returns (bool matched, uint256 registeredTimestamp, uint8 riskScore) {
        require(records[_caseHash].exists, "Case record not found");

        DocumentRecord memory rec = records[_caseHash];
        matched = (rec.documentHash == _documentHash);

        emit DocumentVerified(_caseHash, _documentHash, matched, block.timestamp, msg.sender);

        return (matched, rec.timestamp, rec.riskScore);
    }

    /**
     * @notice Read-only inspection of a recorded document screening
     * @param _caseHash Hash of the case ID
     */
    function getDocumentRecord(bytes32 _caseHash)
        external
        view
        returns (
            bytes32 caseHash,
            bytes32 documentHash,
            bytes32 verificationHash,
            uint8 riskScore,
            uint256 timestamp,
            address registeredBy,
            bool exists
        )
    {
        DocumentRecord memory rec = records[_caseHash];
        return (
            rec.caseHash,
            rec.documentHash,
            rec.verificationHash,
            rec.riskScore,
            rec.timestamp,
            rec.registeredBy,
            rec.exists
        );
    }

    /**
     * @notice Look up a case hash by document hash
     * @param _documentHash SHA-256 hash of the document
     */
    function getCaseByDocumentHash(bytes32 _documentHash)
        external
        view
        returns (bytes32 caseHash)
    {
        return documentToCase[_documentHash];
    }
}
