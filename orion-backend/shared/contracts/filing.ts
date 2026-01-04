export interface IngestionJob {
    cik: string;
    accessionNumber: string;
    url: string;
    ticker: string;
    formType: '6-K' | '10-K';
    date: string;
}
