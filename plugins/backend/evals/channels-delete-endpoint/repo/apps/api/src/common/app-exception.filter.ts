import { ArgumentsHost, Catch, ExceptionFilter, HttpException } from '@nestjs/common';
import { HttpAdapterHost } from '@nestjs/core';
import { AppError } from './app-error';

// The only place an error becomes a response: { error: <code> } with the status from the thrown error.
@Catch()
export class AppExceptionFilter implements ExceptionFilter {
  constructor(private readonly adapterHost: HttpAdapterHost) {}

  catch(exception: unknown, host: ArgumentsHost) {
    const { httpAdapter } = this.adapterHost;
    const res = host.switchToHttp().getResponse();
    if (exception instanceof AppError) {
      return httpAdapter.reply(res, { error: exception.code }, exception.status);
    }
    if (exception instanceof HttpException) {
      const status = exception.getStatus();
      const code = status === 400 ? 'invalid_body' : status === 401 ? 'unauthenticated' : status === 403 ? 'forbidden' : 'http_error';
      return httpAdapter.reply(res, { error: code }, status);
    }
    return httpAdapter.reply(res, { error: 'internal' }, 500);
  }
}
