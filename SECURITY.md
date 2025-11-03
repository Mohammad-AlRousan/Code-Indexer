# Security Policy

**Please do not open public issues for security vulnerabilities.**

## Security Considerations

### API Keys

- **Never commit `.env` files** - Your Azure OpenAI API keys are sensitive
- Use `.env.example` as a template (contains no real credentials)
- Store credentials securely using environment variables or secret managers

### Cache Security

The `.code_index_cache/` directory contains:
- Parsed code signatures (no implementation bodies)
- Embeddings (vector representations of code)
- File paths and metadata

**Note**: While embeddings are mathematical representations, they may still reveal information about your codebase structure. Keep cache files private.

### Best Practices

1. **Don't share `.env` files** - Contains API keys
2. **Don't commit cache directories** - Already in `.gitignore`
3. **Use read-only API keys** if possible
4. **Rotate API keys** periodically
5. **Review access logs** in Azure Portal

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Known Limitations

- Embeddings are stored locally in SQLite (not encrypted)
- API keys are read from environment variables (secure in production environments)
- No built-in rate limiting (relies on Azure OpenAI service limits)

## Updates

Security updates will be announced in GitHub releases and this document.
